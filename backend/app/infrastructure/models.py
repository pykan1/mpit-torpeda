from datetime import datetime
from sqlalchemy import (
    Integer, String, Float, Boolean, DateTime, ForeignKey,
    Text, JSON, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base
from app.domain.entities import UserRole, TripStatus, OrderStatus  # noqa: F401 — used as string values


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.MANAGER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    query_logs: Mapped[list["QueryLog"]] = relationship(back_populates="user")
    saved_reports: Mapped[list["SavedReport"]] = relationship(back_populates="user")


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    region: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    launch_date: Mapped[datetime] = mapped_column(DateTime)

    drivers: Mapped[list["Driver"]] = relationship(back_populates="city")
    trips: Mapped[list["Trip"]] = relationship(back_populates="city")


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    city_id: Mapped[int] = mapped_column(Integer, ForeignKey("cities.id"))
    rating: Mapped[float] = mapped_column(Float, default=5.0)
    total_trips: Mapped[int] = mapped_column(Integer, default=0)
    car_model: Mapped[str] = mapped_column(String(100))
    car_class: Mapped[str] = mapped_column(String(50), default="economy")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    city: Mapped["City"] = relationship(back_populates="drivers")
    trips: Mapped[list["Trip"]] = relationship(back_populates="driver")


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_id: Mapped[int] = mapped_column(Integer, ForeignKey("drivers.id"))
    city_id: Mapped[int] = mapped_column(Integer, ForeignKey("cities.id"))
    status: Mapped[str] = mapped_column(String(20), default=TripStatus.COMPLETED)
    distance_km: Mapped[float] = mapped_column(Float)
    duration_min: Mapped[int] = mapped_column(Integer)
    revenue: Mapped[float] = mapped_column(Float)
    passenger_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    driver: Mapped["Driver"] = relationship(back_populates="trips")
    city: Mapped["City"] = relationship(back_populates="trips")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_id: Mapped[int] = mapped_column(Integer, ForeignKey("cities.id"))
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.COMPLETED)
    amount: Mapped[float] = mapped_column(Float)
    channel: Mapped[str] = mapped_column(String(50), default="app")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    cancel_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)


class SavedReport(Base):
    __tablename__ = "saved_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    natural_query: Mapped[str] = mapped_column(Text)
    sql_query: Mapped[str] = mapped_column(Text)
    chart_type: Mapped[str] = mapped_column(String(50))
    schedule: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "weekly_monday"
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="saved_reports")


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    natural_query: Mapped[str] = mapped_column(Text)
    interpretation: Mapped[str] = mapped_column(Text, default="")
    generated_sql: Mapped[str] = mapped_column(Text, default="")
    ai_thinking: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    guardrail_status: Mapped[str] = mapped_column(String(20), default="ok")
    guardrail_violations: Mapped[list] = mapped_column(JSON, default=list)
    execution_success: Mapped[bool] = mapped_column(Boolean, default=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    execution_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User | None"] = relationship(back_populates="query_logs")


class SemanticTerm(Base):
    __tablename__ = "semantic_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    term: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    sql_expression: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(50), default="metric")
