import httpx
import json
from typing import AsyncIterator
from app.config import settings
from app.domain.exceptions import AIServiceError

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

DB_SCHEMA_DESCRIPTION = """
Database schema for Drivee analytics platform (PostgreSQL):

TABLE: cities
  - id (int, PK)
  - name (varchar) — city name, e.g. "Москва", "Санкт-Петербург", "Казань"
  - region (varchar) — region/federal district
  - is_active (bool)
  - launch_date (timestamp)

TABLE: drivers
  - id (int, PK)
  - full_name (varchar)
  - city_id (int, FK → cities.id)
  - rating (float) — 1.0-5.0
  - total_trips (int)
  - car_model (varchar)
  - car_class (varchar) — 'economy', 'comfort', 'business'
  - is_active (bool)
  - joined_at (timestamp)

TABLE: trips
  - id (int, PK)
  - city_id (int)
  - order_id (varchar, anonymized order ID)
  - tender_id (varchar, nullable)
  - user_id (varchar, anonymized user ID)
  - driver_id (varchar, nullable, anonymized driver ID)
  - offset_hours (int) — city local offset from UTC
  - status_order (varchar) — final order status: done/cancel/delete/accept
  - status_tender (varchar, nullable) — tender status
  - order_timestamp (timestamp)
  - tender_timestamp (timestamp, nullable)
  - driveraccept_timestamp (timestamp, nullable)
  - driverarrived_timestamp (timestamp, nullable)
  - driverstarttheride_timestamp (timestamp, nullable)
  - driverdone_timestamp (timestamp, nullable)
  - clientcancel_timestamp (timestamp, nullable)
  - drivercancel_timestamp (timestamp, nullable)
  - order_modified_local (timestamp, nullable)
  - cancel_before_accept_local (timestamp, nullable)
  - distance_in_meters (float)
  - duration_in_seconds (int)
  - price_order_local (float) — final order price in local currency
  - price_tender_local (float, nullable)
  - price_start_local (float)

TABLE: orders
  - id (int, PK)
  - city_id (int, FK → cities.id)
  - status (enum: 'active','completed','cancelled')
  - amount (float) — order amount in rubles
  - channel (varchar) — 'app', 'web', 'partner'
  - created_at (timestamp)
  - cancel_reason (varchar, nullable)

TABLE: users
  - id (int, PK)
  - name (varchar)
  - email (varchar)
  - role (enum: 'admin','analyst','manager','viewer')
  - is_active (bool)
  - created_at (timestamp)

TABLE: saved_reports
  - id (int, PK)
  - user_id (int, FK → users.id)
  - title (varchar)
  - natural_query (text)
  - sql_query (text)
  - chart_type (varchar)
  - schedule (varchar, nullable) — 'weekly_monday', 'daily', etc.
  - is_public (bool)
  - created_at (timestamp)

TABLE: query_logs
  - id (int, PK)
  - user_id (int, nullable)
  - natural_query (text)
  - interpretation (text)
  - generated_sql (text)
  - confidence (float)
  - guardrail_status (varchar)
  - execution_success (bool)
  - row_count (int)
  - created_at (timestamp)

TABLE: semantic_terms
  - id (int, PK)
  - term (varchar) — e.g. "выручка", "отмены", "поездки"
  - aliases (json array) — synonyms
  - sql_expression (text) — how to express in SQL
  - description (text)
  - category (varchar) — 'metric', 'dimension', 'filter'
"""

SEMANTIC_LAYER = {
    "выручка": "SUM(trips.price_order_local)",
    "доход": "SUM(trips.price_order_local)",
    "revenue": "SUM(trips.price_order_local)",
    "поездки": "COUNT(DISTINCT trips.order_id)",
    "trips": "COUNT(DISTINCT trips.order_id)",
    "отмены": "COUNT(*) FILTER (WHERE trips.status_order = 'cancel')",
    "cancelled": "COUNT(*) FILTER (WHERE trips.status_order = 'cancel')",
    "средний чек": "AVG(trips.price_order_local)",
    "длительность": "AVG(trips.duration_in_seconds)",
    "расстояние": "AVG(trips.distance_in_meters)",
    "водители": "COUNT(DISTINCT trips.driver_id)",
    "питер": "Санкт-Петербург",
    "спб": "Санкт-Петербург",
    "мск": "Москва",
}


def build_system_prompt() -> str:
    semantic_str = "\n".join(f"  - '{k}' → {v}" for k, v in SEMANTIC_LAYER.items())
    return f"""Ты Driveery — интеллектуальный генератор SQL для аналитики сервиса Drivee.

{DB_SCHEMA_DESCRIPTION}

СЕМАНТИЧЕСКИЙ СЛОЙ (словарь бизнес-терминов):
{semantic_str}

ПРАВИЛА:
1. Генерируй ТОЛЬКО SELECT-запросы. Никогда не используй DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE.
2. Никогда не выбирай чувствительные колонки: password, token, secret.
3. Всегда добавляй LIMIT 1000, если это не агрегирующий запрос.
4. Используй семантический слой, когда пользователь упоминает бизнес-термины.
5. Для анализа поездок в первую очередь используй таблицу trips.
6. Для фильтров по времени используй NOW(), CURRENT_DATE, INTERVAL.
7. "прошлая неделя" = WHERE order_timestamp >= NOW() - INTERVAL '14 days' AND order_timestamp < NOW() - INTERVAL '7 days'
8. "эта неделя" = WHERE order_timestamp >= NOW() - INTERVAL '7 days'
9. "вчера" = WHERE DATE(order_timestamp) = CURRENT_DATE - 1

ОТВЕЧАЙ СТРОГО В ТАКОМ JSON-ФОРМАТЕ:
{{
  "interpretation": "Пояснение на русском, как ты понял запрос",
  "sql": "SELECT ... FROM ... WHERE ... ORDER BY ... LIMIT ...",
  "chart_type": "bar|line|pie|doughnut|table|kpi",
  "confidence": 0.0-1.0,
  "chart_config": {{
    "x_column": "имя колонки для оси X",
    "y_column": "имя колонки для оси Y",
    "label_column": "имя колонки для labels (опционально)"
  }}
}}

ВАЖНО ДЛЯ REASONING (ОБЯЗАТЕЛЬНО):
- Пиши reasoning/think строго на русском языке.
- Запрещено использовать английские фразы, кроме SQL-ключевых слов, названий таблиц/колонок и технических токенов SQL.
- Никогда не пиши служебные заголовки и мета-текст: "CHAIN OF THOUGHT", "Here is my thinking", "[Done]", "Final check" и т.п.
- Не дублируй и не повторяй один и тот же шаг разными формулировками.
- Не выводи markdown-блоки в reasoning.
- В content верни только валидный JSON, без дополнительного текста.
"""


def _build_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://driveery.app",
        "X-Title": "Driveery NL2SQL",
    }


def _build_payload(natural_query: str, stream: bool = False) -> dict:
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": natural_query},
        ],
        "temperature": 0.1,
        "include_reasoning": True,
    }
    if stream:
        payload["stream"] = True
    return payload


def _parse_ai_content(raw_content: str) -> dict:
    # Parse JSON from content (may be wrapped in ```json ... ```)
    content = raw_content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON block
        import re

        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise AIServiceError(f"Could not parse AI JSON response: {content[:200]}")


async def generate_sql(natural_query: str) -> dict:
    """Call OpenRouter API with thinking enabled and return parsed response."""
    headers = _build_headers()
    payload = _build_payload(natural_query)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AIServiceError(f"OpenRouter HTTP error: {e.response.status_code} — {e.response.text}")
        except httpx.RequestError as e:
            raise AIServiceError(f"OpenRouter connection error: {str(e)}")

    data = resp.json()
    choice = data["choices"][0]["message"]
    raw_content = choice.get("content", "")
    thinking = choice.get("reasoning_content", "") or choice.get("reasoning", "")
    parsed = _parse_ai_content(raw_content)

    parsed["thinking"] = thinking
    return parsed


async def stream_generate_sql(natural_query: str) -> AsyncIterator[dict]:
    """
    Stream AI generation from OpenRouter.
    Yields:
      - {"type": "thinking", "delta": "..."} in real time
      - {"type": "result", "data": parsed_json} when completed
    """
    headers = _build_headers()
    payload = _build_payload(natural_query, stream=True)

    thinking_parts: list[str] = []
    content_parts: list[str] = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream(
                "POST",
                f"{OPENROUTER_BASE}/chat/completions",
                headers=headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue

                    payload_line = line[5:].strip()
                    if payload_line == "[DONE]":
                        break

                    try:
                        chunk = json.loads(payload_line)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk.get("choices") or []
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    if not isinstance(delta, dict):
                        continue

                    reasoning_delta = (
                        delta.get("reasoning_content")
                        or delta.get("reasoning")
                        or ""
                    )
                    if reasoning_delta:
                        thinking_parts.append(reasoning_delta)
                        yield {"type": "thinking", "delta": reasoning_delta}

                    content_delta = delta.get("content") or ""
                    if content_delta:
                        content_parts.append(content_delta)
        except httpx.HTTPStatusError as e:
            raise AIServiceError(f"OpenRouter HTTP error: {e.response.status_code} — {e.response.text}")
        except httpx.RequestError as e:
            raise AIServiceError(f"OpenRouter connection error: {str(e)}")

    raw_content = "".join(content_parts).strip()
    if not raw_content:
        raise AIServiceError("OpenRouter streaming returned empty content")

    parsed = _parse_ai_content(raw_content)
    parsed["thinking"] = "".join(thinking_parts).strip()
    yield {"type": "result", "data": parsed}
