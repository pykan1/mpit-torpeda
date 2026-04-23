import time
from datetime import datetime
from typing import AsyncIterator, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.domain.entities import NL2SQLResponse, QueryResult, GuardrailSeverity, GuardrailReport, ChartType
from app.domain.exceptions import GuardrailViolation, SQLExecutionError
from app.infrastructure.ai.openrouter_client import generate_sql, stream_generate_sql
from app.application.security_service import validate_sql
from app.application.chart_service import auto_select_chart, build_chart_data
from app.application.query_intent_service import is_out_of_scope_query, build_fallback_ai_result
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
    if is_out_of_scope_query(natural_query):
        ai_result = build_fallback_ai_result()
    else:
        ai_result = await generate_sql(natural_query)
    return await _finalize_nl_query(natural_query, ai_result, db, user_id)


def _serialize_response(resp: NL2SQLResponse) -> dict[str, Any]:
    result_out = None
    if resp.result:
        result_out = {
            "columns": resp.result.columns,
            "rows": resp.result.rows,
            "row_count": resp.result.row_count,
            "chart_type": resp.result.chart_type.value,
            "chart_data": resp.result.chart_data,
        }

    return {
        "natural_query": resp.natural_query,
        "interpretation": resp.interpretation,
        "sql": resp.sql,
        "thinking": resp.thinking,
        "guardrail": {
            "severity": resp.guardrail.severity.value,
            "violations": resp.guardrail.violations,
            "warnings": resp.guardrail.warnings,
        },
        "result": result_out,
        "confidence": resp.confidence,
        "query_log_id": resp.query_log_id,
        "is_fallback": resp.is_fallback,
    }


async def process_nl_query_stream(
    natural_query: str,
    db: AsyncSession,
    user_id: int | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Stream AI thinking in real time, then execute SQL and return final payload."""
    if is_out_of_scope_query(natural_query):
        response = await _finalize_nl_query(
            natural_query,
            build_fallback_ai_result(),
            db,
            user_id,
        )
        yield {"type": "final", "data": _serialize_response(response)}
        return

    ai_result = None
    async for event in stream_generate_sql(natural_query):
        if event.get("type") == "thinking":
            yield event
        elif event.get("type") == "result":
            ai_result = event.get("data")

    if not ai_result:
        raise SQLExecutionError("AI did not return a final result")

    response = await _finalize_nl_query(natural_query, ai_result, db, user_id)
    yield {"type": "final", "data": _serialize_response(response)}


async def _finalize_nl_query(
    natural_query: str,
    ai_result: dict[str, Any],
    db: AsyncSession,
    user_id: int | None = None,
) -> NL2SQLResponse:

    sql = ai_result.get("sql", "").strip()
    interpretation = ai_result.get("interpretation", "")
    thinking = ai_result.get("thinking", "")
    confidence = float(ai_result.get("confidence", 0.8))
    suggested_chart = ai_result.get("chart_type")
    chart_config = ai_result.get("chart_config")
    is_fallback = bool(ai_result.get("is_fallback", False))

    if is_fallback:
        guardrail = GuardrailReport(
            severity=GuardrailSeverity.WARNING,
            violations=[],
            warnings=["Запрос вне области SQL-аналитики Drivee. Выполнение SQL пропущено."],
        )
    else:
        guardrail = validate_sql(sql)

    result = None
    execution_success = False
    row_count = 0
    execution_ms = 0

    if not is_fallback and guardrail.severity != GuardrailSeverity.BLOCKED:
        start = time.monotonic()
        try:
            raw = await db.execute(text(sql))
            columns = list(raw.keys())
            rows = [list(r) for r in raw.fetchall()]
            execution_ms = int((time.monotonic() - start) * 1000)
            row_count = len(rows)
            execution_success = True

            chart_type = auto_select_chart(
                columns,
                rows,
                suggested_chart,
                natural_query=natural_query,
            )
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
        is_fallback=is_fallback,
    )
