import re
from app.domain.entities import GuardrailReport, GuardrailSeverity
from app.domain.exceptions import GuardrailViolation

FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE", "ALTER", "UPDATE", "INSERT",
    "GRANT", "REVOKE", "CREATE", "EXEC", "EXECUTE", "CALL",
    "--", "/*", "*/", "xp_", "sp_",
]

SENSITIVE_COLUMNS = [
    "password", "passwd", "token", "secret", "api_key",
    "phone", "phone_number", "email",
]

ALLOWED_TABLES = [
    "trips", "orders", "cities", "drivers",
    "saved_reports", "query_logs", "semantic_terms",
]

MAX_QUERY_LENGTH = 5000


def validate_sql(sql: str) -> GuardrailReport:
    """
    Validate AI-generated SQL against security rules.
    Returns GuardrailReport — caller must check severity before execution.
    """
    violations = []
    warnings = []
    sql_upper = sql.upper()
    sql_lower = sql.lower()

    if len(sql) > MAX_QUERY_LENGTH:
        violations.append(f"Query too long ({len(sql)} chars, max {MAX_QUERY_LENGTH})")

    for kw in FORBIDDEN_KEYWORDS:
        pattern = r'\b' + re.escape(kw.upper()) + r'\b'
        if re.search(pattern, sql_upper):
            violations.append(f"Forbidden keyword detected: {kw}")

    for col in SENSITIVE_COLUMNS:
        if col in sql_lower:
            violations.append(f"Sensitive column access blocked: {col}")

    if not sql_upper.strip().startswith("SELECT"):
        violations.append("Only SELECT statements are allowed")

    if ";" in sql:
        count = sql.count(";")
        stripped = sql.strip()
        if count > 1 or (count == 1 and not stripped.endswith(";")):
            violations.append("Multiple statements detected (SQL injection risk)")

    if "LIMIT" not in sql_upper:
        warnings.append("No LIMIT clause — query may return large result set")

    if violations:
        return GuardrailReport(
            severity=GuardrailSeverity.BLOCKED,
            violations=violations,
            warnings=warnings,
        )

    if warnings:
        return GuardrailReport(
            severity=GuardrailSeverity.WARNING,
            violations=[],
            warnings=warnings,
        )

    return GuardrailReport(severity=GuardrailSeverity.OK, violations=[], warnings=[])
