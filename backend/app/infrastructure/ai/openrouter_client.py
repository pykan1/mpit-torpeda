import httpx
import json
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
  - driver_id (int, FK → drivers.id)
  - city_id (int, FK → cities.id)
  - status (enum: 'pending','in_progress','completed','cancelled')
  - distance_km (float)
  - duration_min (int)
  - revenue (float) — trip revenue in rubles
  - passenger_rating (float, nullable)
  - started_at (timestamp)
  - ended_at (timestamp, nullable)
  - cancel_reason (varchar, nullable)

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
    "выручка": "SUM(trips.revenue)",
    "доход": "SUM(trips.revenue)",
    "revenue": "SUM(trips.revenue)",
    "поездки": "COUNT(trips.id)",
    "trips": "COUNT(trips.id)",
    "отмены": "COUNT(trips.id) FILTER (WHERE trips.status = 'cancelled')",
    "cancelled": "COUNT(trips.id) FILTER (WHERE trips.status = 'cancelled')",
    "отменённые заказы": "COUNT(orders.id) FILTER (WHERE orders.status = 'cancelled')",
    "водители": "COUNT(DISTINCT drivers.id)",
    "активные водители": "COUNT(DISTINCT drivers.id) FILTER (WHERE drivers.is_active = true)",
    "рейтинг": "AVG(drivers.rating)",
    "питер": "Санкт-Петербург",
    "спб": "Санкт-Петербург",
    "мск": "Москва",
}


def build_system_prompt() -> str:
    semantic_str = "\n".join(f"  - '{k}' → {v}" for k, v in SEMANTIC_LAYER.items())
    return f"""You are Driveery — an intelligent SQL generator for Drivee ride-sharing analytics.

{DB_SCHEMA_DESCRIPTION}

SEMANTIC LAYER (business terms dictionary):
{semantic_str}

RULES:
1. Generate ONLY SELECT queries. Never use DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE.
2. Never select sensitive columns: password, token, secret.
3. Always add LIMIT 1000 unless aggregating.
4. Use the semantic layer when the user mentions business terms.
5. Always use proper JOINs based on FK relationships.
6. For time filters: use NOW(), CURRENT_DATE, INTERVAL.
7. "прошлая неделя" = WHERE started_at >= NOW() - INTERVAL '14 days' AND started_at < NOW() - INTERVAL '7 days'
8. "эта неделя" = WHERE started_at >= NOW() - INTERVAL '7 days'
9. "вчера" = WHERE DATE(started_at) = CURRENT_DATE - 1

RESPOND IN THIS EXACT JSON FORMAT:
{{
  "interpretation": "Human-readable explanation of how you understood the query in Russian",
  "sql": "SELECT ... FROM ... WHERE ... ORDER BY ... LIMIT ...",
  "chart_type": "bar|line|pie|doughnut|table|kpi",
  "confidence": 0.0-1.0,
  "chart_config": {{
    "x_column": "column name for X axis",
    "y_column": "column name for Y axis",
    "label_column": "column name for labels (optional)"
  }}
}}

Think step by step before answering."""


async def generate_sql(natural_query: str) -> dict:
    """Call OpenRouter API with thinking enabled and return parsed response."""
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://driveery.app",
        "X-Title": "Driveery NL2SQL",
    }

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": natural_query},
        ],
        "temperature": 0.1,
        "include_reasoning": True,
    }

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

    # Parse JSON from content (may be wrapped in ```json ... ```)
    content = raw_content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON block
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
        else:
            raise AIServiceError(f"Could not parse AI JSON response: {content[:200]}")

    parsed["thinking"] = thinking
    return parsed
