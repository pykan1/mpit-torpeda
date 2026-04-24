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
    manual_approval: bool = False,
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
    prepared = await prepare_nl_query(natural_query, user_id=user_id)
    if manual_approval and not prepared.is_fallback:
        prepared.awaiting_manual_execution = True
        return prepared
    return await execute_prepared_sql_response(prepared, db, user_id)


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
        "awaiting_manual_execution": resp.awaiting_manual_execution,
    }


async def process_nl_query_stream(
    natural_query: str,
    db: AsyncSession,
    user_id: int | None = None,
    manual_approval: bool = False,
) -> AsyncIterator[dict[str, Any]]:
    """Stream AI thinking in real time, then execute SQL and return final payload."""
    if is_out_of_scope_query(natural_query):
        prepared = await prepare_nl_query(natural_query, user_id=user_id)
        response = await execute_prepared_sql_response(prepared, db, user_id)
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

    prepared = _build_prepared_response(natural_query, ai_result)
    if manual_approval and not prepared.is_fallback:
        prepared.awaiting_manual_execution = True
        response = prepared
    else:
        response = await execute_prepared_sql_response(prepared, db, user_id)
    yield {"type": "final", "data": _serialize_response(response)}


async def prepare_nl_query(
    natural_query: str,
    user_id: int | None = None,
) -> NL2SQLResponse:
    if is_out_of_scope_query(natural_query):
        ai_result = build_fallback_ai_result()
    else:
        ai_result = await generate_sql(natural_query)
    return _build_prepared_response(natural_query, ai_result)


def _build_prepared_response(
    natural_query: str,
    ai_result: dict[str, Any],
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

    return NL2SQLResponse(
        natural_query=natural_query,
        interpretation=interpretation,
        sql=sql,
        thinking=thinking,
        guardrail=guardrail,
        result=None,
        confidence=confidence,
        query_log_id=None,
        is_fallback=is_fallback,
    )


async def execute_prepared_sql_response(
    prepared: NL2SQLResponse,
    db: AsyncSession,
    user_id: int | None = None,
) -> NL2SQLResponse:
    # Guardrails are always re-evaluated server-side right before execution.
    guardrail = prepared.guardrail if prepared.is_fallback else validate_sql(prepared.sql)
    result = None
    execution_success = False
    row_count = 0
    execution_ms = 0

    if not prepared.is_fallback and guardrail.severity != GuardrailSeverity.BLOCKED:
        start = time.monotonic()
        try:
            raw = await db.execute(text(prepared.sql))
            columns = list(raw.keys())
            rows = [list(r) for r in raw.fetchall()]
            execution_ms = int((time.monotonic() - start) * 1000)
            row_count = len(rows)
            execution_success = True

            chart_type = auto_select_chart(
                columns,
                rows,
                None,
                natural_query=prepared.natural_query,
            )
            chart_data = build_chart_data(columns, rows, chart_type, None)

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
        natural_query=prepared.natural_query,
        interpretation=prepared.interpretation,
        generated_sql=prepared.sql,
        ai_thinking=prepared.thinking,
        confidence=prepared.confidence,
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
        natural_query=prepared.natural_query,
        interpretation=prepared.interpretation,
        sql=prepared.sql,
        thinking=prepared.thinking,
        guardrail=guardrail,
        result=result,
        confidence=prepared.confidence,
        query_log_id=log.id,
        is_fallback=prepared.is_fallback,
        awaiting_manual_execution=False,
    )
