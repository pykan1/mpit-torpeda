import re


ANALYTICS_HINTS = (
    "sql",
    "select",
    "запрос",
    "таблиц",
    "баз",
    "данн",
    "аналит",
    "метрик",
    "дашборд",
    "отчет",
    "отчёт",
    "выручк",
    "доход",
    "поезд",
    "trip",
    "driver",
    "водител",
    "город",
    "citie",
    "заказ",
    "order",
    "отмен",
    "rating",
    "revenue",
)

OFFTOPIC_HINTS = (
    "инвест",
    "недвижим",
    "движим",
    "акци",
    "крипт",
    "биткоин",
    "кредит",
    "ипотек",
    "депозит",
    "курс валют",
    "финансов",
    "ignore previous",
    "forget previous",
    "забудь все",
    "забудь предыдущ",
    "jailbreak",
    "я твой админ",
    "слушай только",
    "иначе",
    "угрож",
)


def is_out_of_scope_query(natural_query: str) -> bool:
    text = (natural_query or "").strip().lower()
    if not text:
        return True

    has_analytics_signal = any(hint in text for hint in ANALYTICS_HINTS)
    offtopic_hits = sum(1 for hint in OFFTOPIC_HINTS if hint in text)

    # Obvious prompt-injection / role override.
    if re.search(r"(ignore|forget).{0,40}(instruction|settings|prompt)", text):
        return True

    # Strongly off-topic with no analytics intent.
    if offtopic_hits >= 1 and not has_analytics_signal:
        return True

    # Generic non-analytics advisory request.
    if not has_analytics_signal and re.search(r"(что выбрать|посоветуй|как лучше|что делать)", text):
        return True

    return False


def build_fallback_ai_result() -> dict:
    return {
        "interpretation": (
            "Запрос не относится к аналитике сервиса Drivee. Я — Driveery, "
            "генератор SQL-запросов для работы с базой данных платформы. "
            "Финансовые консультации и инвестиционные советы выходят за рамки моих функций. "
            "Сформулируйте запрос по данным Drivee: выручка, поездки, отмены, водители, города."
        ),
        "sql": "",
        "chart_type": "table",
        "confidence": 0.2,
        "chart_config": {},
        "thinking": "",
        "is_fallback": True,
    }
