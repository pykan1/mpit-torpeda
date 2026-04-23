from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    MANAGER = "manager"
    VIEWER = "viewer"


class TripStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    TABLE = "table"
    KPI = "kpi"


class GuardrailSeverity(str, Enum):
    BLOCKED = "blocked"
    WARNING = "warning"
    OK = "ok"


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    chart_type: ChartType
    chart_data: dict[str, Any]


@dataclass
class GuardrailReport:
    severity: GuardrailSeverity
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class NL2SQLResponse:
    natural_query: str
    interpretation: str
    sql: str
    thinking: str
    guardrail: GuardrailReport
    result: QueryResult | None
    confidence: float
    query_log_id: int | None = None
