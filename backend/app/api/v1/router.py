from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.infrastructure.database import get_db
from app.infrastructure.models import (
    QueryLog, SavedReport, User, Driver, Trip, SemanticTerm
)
from app.application.nl2sql_service import process_nl_query, process_nl_query_stream
from app.application.security_service import validate_sql
from app.domain.exceptions import DriveeryException, GuardrailViolation, SQLExecutionError
from app.api.v1.schemas import (
    NLQueryRequest, NLQueryResponse, SaveReportRequest, SavedReportOut,
    QueryLogOut, UserOut, SemanticTermOut, StatsOut, GuardrailReportOut, QueryResultOut
)

router = APIRouter()


# ─── NL2SQL ───────────────────────────────────────────────────────────────────

@router.post("/query", response_model=NLQueryResponse, tags=["NL2SQL"])
async def run_nl_query(req: NLQueryRequest, db: AsyncSession = Depends(get_db)):
    """Translate natural language to SQL, execute, and return results with AI thinking."""
    try:
        resp = await process_nl_query(req.query, db, req.user_id)
    except DriveeryException as e:
        raise HTTPException(status_code=400, detail={"error": e.message, "code": e.code})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "code": "INTERNAL"})

    result_out = None
    if resp.result:
        result_out = QueryResultOut(
            columns=resp.result.columns,
            rows=resp.result.rows,
            row_count=resp.result.row_count,
            chart_type=resp.result.chart_type.value,
            chart_data=resp.result.chart_data,
        )

    return NLQueryResponse(
        natural_query=resp.natural_query,
        interpretation=resp.interpretation,
        sql=resp.sql,
        thinking=resp.thinking,
        guardrail=GuardrailReportOut(
            severity=resp.guardrail.severity.value,
            violations=resp.guardrail.violations,
            warnings=resp.guardrail.warnings,
        ),
        result=result_out,
        confidence=resp.confidence,
        query_log_id=resp.query_log_id,
        is_fallback=resp.is_fallback,
    )


@router.post("/query/stream", tags=["NL2SQL"])
async def run_nl_query_stream(req: NLQueryRequest, db: AsyncSession = Depends(get_db)):
    """Stream AI thinking in real time and send final NL2SQL result as SSE."""

    async def event_generator():
        try:
            async for event in process_nl_query_stream(req.query, db, req.user_id):
                event_payload = jsonable_encoder(event)
                yield f"data: {json.dumps(event_payload, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except DriveeryException as e:
            error_event = {"type": "error", "error": e.message, "code": e.code}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_event = {"type": "error", "error": str(e), "code": "INTERNAL"}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/validate-sql", tags=["Security"])
async def validate_sql_endpoint(payload: dict):
    """Validate raw SQL against guardrails without executing."""
    sql = payload.get("sql", "")
    report = validate_sql(sql)
    return {
        "severity": report.severity.value,
        "violations": report.violations,
        "warnings": report.warnings,
    }


# ─── Reports ──────────────────────────────────────────────────────────────────

@router.post("/reports", response_model=SavedReportOut, tags=["Reports"])
async def save_report(req: SaveReportRequest, db: AsyncSession = Depends(get_db)):
    """Save a query as a reusable report."""
    report = SavedReport(
        user_id=req.user_id,
        title=req.title,
        natural_query=req.natural_query,
        sql_query=req.sql_query,
        chart_type=req.chart_type,
        schedule=req.schedule,
        is_public=req.is_public,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/reports", response_model=list[SavedReportOut], tags=["Reports"])
async def list_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SavedReport).order_by(SavedReport.created_at.desc()).limit(50))
    return result.scalars().all()


@router.delete("/reports/{report_id}", tags=["Reports"])
async def delete_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SavedReport).where(SavedReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await db.delete(report)
    await db.commit()
    return {"ok": True}


@router.post("/reports/{report_id}/run", response_model=NLQueryResponse, tags=["Reports"])
async def run_saved_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """Re-execute a saved report."""
    result = await db.execute(select(SavedReport).where(SavedReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return await run_nl_query(NLQueryRequest(query=report.natural_query), db)


# ─── Query Logs ───────────────────────────────────────────────────────────────

@router.get("/logs", response_model=list[QueryLogOut], tags=["Audit"])
async def list_logs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(QueryLog).order_by(QueryLog.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.get("/logs/{log_id}", response_model=QueryLogOut, tags=["Audit"])
async def get_log(log_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QueryLog).where(QueryLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log


# ─── Security / Users ─────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserOut], tags=["Security"])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.patch("/users/{user_id}/role", response_model=UserOut, tags=["Security"])
async def update_user_role(user_id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_role = payload.get("role")
    if new_role:
        user.role = new_role
        await db.commit()
        await db.refresh(user)
    return user


# ─── Semantic Layer ───────────────────────────────────────────────────────────

@router.get("/semantic", response_model=list[SemanticTermOut], tags=["Semantic"])
async def list_terms(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SemanticTerm).order_by(SemanticTerm.term))
    return result.scalars().all()


@router.post("/semantic", response_model=SemanticTermOut, tags=["Semantic"])
async def create_term(payload: dict, db: AsyncSession = Depends(get_db)):
    term = SemanticTerm(
        term=payload["term"],
        aliases=payload.get("aliases", []),
        sql_expression=payload["sql_expression"],
        description=payload.get("description", ""),
        category=payload.get("category", "metric"),
    )
    db.add(term)
    await db.commit()
    await db.refresh(term)
    return term


# ─── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsOut, tags=["Analytics"])
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_q = await db.scalar(select(func.count(QueryLog.id)))
    success_q = await db.scalar(select(func.count(QueryLog.id)).where(QueryLog.execution_success == True))
    blocked_q = await db.scalar(
        select(func.count(QueryLog.id)).where(QueryLog.guardrail_status == "blocked")
    )
    total_r = await db.scalar(select(func.count(SavedReport.id)))
    total_d = await db.scalar(select(func.count(Driver.id)))
    total_t = await db.scalar(select(func.count(Trip.id)))
    total_rev = await db.scalar(select(func.sum(Trip.revenue))) or 0.0

    return StatsOut(
        total_queries=total_q or 0,
        successful_queries=success_q or 0,
        blocked_queries=blocked_q or 0,
        total_reports=total_r or 0,
        total_drivers=total_d or 0,
        total_trips=total_t or 0,
        total_revenue=float(total_rev),
    )


# ─── Template Queries ─────────────────────────────────────────────────────────

@router.get("/templates", tags=["Templates"])
async def get_templates():
    return [
        {
            "id": 1,
            "title": "Топ-3 города по отменам",
            "query": "Топ-3 города по количеству отменённых поездок за эту неделю",
            "icon": "🗺️",
            "category": "trips",
        },
        {
            "id": 2,
            "title": "Выручка по неделям",
            "query": "Покажи выручку по неделям за последние 2 месяца",
            "icon": "💰",
            "category": "revenue",
        },
        {
            "id": 3,
            "title": "Активные водители по городам",
            "query": "Сколько активных водителей в каждом городе",
            "icon": "🚗",
            "category": "drivers",
        },
        {
            "id": 4,
            "title": "Сравни поездки: эта vs прошлая неделя",
            "query": "Сравни количество поездок в Москве за эту и прошлую неделю",
            "icon": "📊",
            "category": "comparison",
        },
        {
            "id": 5,
            "title": "Средний рейтинг водителей",
            "query": "Средний рейтинг водителей по городам",
            "icon": "⭐",
            "category": "drivers",
        },
        {
            "id": 6,
            "title": "Отмены по причинам",
            "query": "Топ причин отмены поездок за последний месяц",
            "icon": "❌",
            "category": "cancellations",
        },
    ]
