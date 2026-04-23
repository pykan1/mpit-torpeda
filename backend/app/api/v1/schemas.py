from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Any


class NLQueryRequest(BaseModel):
    query: str
    user_id: int | None = None


class GuardrailReportOut(BaseModel):
    severity: str
    violations: list[str]
    warnings: list[str]


class QueryResultOut(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    chart_type: str
    chart_data: dict[str, Any]


class NLQueryResponse(BaseModel):
    natural_query: str
    interpretation: str
    sql: str
    thinking: str
    guardrail: GuardrailReportOut
    result: QueryResultOut | None
    confidence: float
    query_log_id: int | None
    is_fallback: bool = False


class SaveReportRequest(BaseModel):
    title: str
    natural_query: str
    sql_query: str
    chart_type: str
    user_id: int | None = None
    schedule: str | None = None
    is_public: bool = False


class SavedReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    natural_query: str
    sql_query: str
    chart_type: str
    schedule: str | None
    is_public: bool
    created_at: datetime
    last_run_at: datetime | None


class QueryLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    natural_query: str
    interpretation: str
    generated_sql: str
    ai_thinking: str
    confidence: float
    guardrail_status: str
    guardrail_violations: list[Any]
    execution_success: bool
    row_count: int
    execution_ms: int
    created_at: datetime


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class SemanticTermOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    term: str
    aliases: list[str]
    sql_expression: str
    description: str
    category: str


class StatsOut(BaseModel):
    total_queries: int
    successful_queries: int
    blocked_queries: int
    total_reports: int
    total_drivers: int
    total_trips: int
    total_revenue: float
