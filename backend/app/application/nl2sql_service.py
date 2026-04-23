import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.domain.entities import NL2SQLResponse, QueryResult, GuardrailSeverity, ChartType
from app.domain.exceptions import GuardrailViolation, SQLExecutionError
from app.infrastructure.ai.openrouter_client import generate_sql
from app.application.security_service import validate_sql
from app.application.chart_service import auto_select_chart, build_chart_data
from app.infrastructure.models import QueryLog


async def process_nl_query(
    natural_query: str,
    db: AsyncSession,
    user_id: int | None = None,
) -> NL2SQLResponse:
    """
    Main use case: natural language → SQL → execution → chart.
    Steps:
    1. Call AI to generate SQL + interpretation + thinking
    2. Run guardrails
    3. Execute SQL (if not blocked)
    4. Build chart data
    5. Log everything
    """
    ai_result = await generate_sql(natural_query)

    sql = ai_result.get("sql", "").strip()
    interpretation = ai_result.get("interpretation", "")
    thinking = ai_result.get("thinking", "")
    confidence = float(ai_result.get("confidence", 0.8))
    suggested_chart = ai_result.get("chart_type")
    chart_config = ai_result.get("chart_config")

    guardrail = validate_sql(sql)

    result = None
    execution_success = False
    row_count = 0
    execution_ms = 0

    if guardrail.severity != GuardrailSeverity.BLOCKED:
        start = time.monotonic()
        try:
            raw = await db.execute(text(sql))
            columns = list(raw.keys())
            rows = [list(r) for r in raw.fetchall()]
            execution_ms = int((time.monotonic() - start) * 1000)
            row_count = len(rows)
            execution_success = True

            chart_type = auto_select_chart(columns, rows, suggested_chart)
            chart_data = build_chart_data(columns, rows, chart_type, chart_config)

            result = QueryResult(
                columns=columns,
                rows=rows,
                row_count=row_count,
                chart_type=chart_type,
                chart_data=chart_data,
            )
        except Exception as e:
            execution_ms = int((time.monotonic() - start) * 1000)
            raise SQLExecutionError(str(e))

    log = QueryLog(
        user_id=user_id,
        natural_query=natural_query,
        interpretation=interpretation,
        generated_sql=sql,
        ai_thinking=thinking,
        confidence=confidence,
        guardrail_status=guardrail.severity.value,
        guardrail_violations=guardrail.violations,
        execution_success=execution_success,
        row_count=row_count,
        execution_ms=execution_ms,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    return NL2SQLResponse(
        natural_query=natural_query,
        interpretation=interpretation,
        sql=sql,
        thinking=thinking,
        guardrail=guardrail,
        result=result,
        confidence=confidence,
        query_log_id=log.id,
    )
