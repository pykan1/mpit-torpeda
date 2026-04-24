from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, insert, inspect
from pathlib import Path
from datetime import datetime
import csv

from app.config import settings
from app.api.v1.router import router
from app.infrastructure.database import engine, Base
from app.infrastructure.models import Trip

app = FastAPI(
    title="Driveery API",
    description="NL2SQL analytics platform for Drivee",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_trips_table_if_needed)
    await seed_database()


def _migrate_trips_table_if_needed(sync_conn) -> None:
    """
    Perform a lightweight schema migration for `trips` only.
    We recreate `trips` when legacy columns are detected.
    """
    inspector = inspect(sync_conn)
    if "trips" not in inspector.get_table_names():
        return

    actual_cols = {c["name"] for c in inspector.get_columns("trips")}
    required_cols = {
        "id", "city_id", "order_id", "tender_id", "user_id", "driver_id",
        "offset_hours", "status_order", "status_tender",
        "order_timestamp", "tender_timestamp", "driveraccept_timestamp",
        "driverarrived_timestamp", "driverstarttheride_timestamp",
        "driverdone_timestamp", "clientcancel_timestamp",
        "drivercancel_timestamp", "order_modified_local",
        "cancel_before_accept_local", "distance_in_meters",
        "duration_in_seconds", "price_order_local",
        "price_tender_local", "price_start_local",
    }
    legacy_cols = {"distance_km", "duration_min", "revenue", "started_at", "status"}

    need_recreate = not required_cols.issubset(actual_cols) or bool(actual_cols & legacy_cols)
    if need_recreate:
        Trip.__table__.drop(sync_conn, checkfirst=True)
        Trip.__table__.create(sync_conn, checkfirst=True)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _find_train_csv_path() -> Path | None:
    candidates = [
        Path(settings.TRAIN_CSV_PATH),
        Path("/app/train.csv"),
        Path(__file__).resolve().parents[2] / "train.csv",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


async def _load_trips_from_csv(db, csv_path: Path, batch_size: int = 5000) -> int:
    inserted = 0
    batch: list[dict] = []

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item = {
                "city_id": int(row["city_id"]) if row["city_id"] else 0,
                "order_id": row["order_id"],
                "tender_id": row["tender_id"] or None,
                "user_id": row["user_id"],
                "driver_id": row["driver_id"] or None,
                "offset_hours": int(row["offset_hours"]) if row["offset_hours"] else 0,
                "status_order": row["status_order"] or "unknown",
                "status_tender": row["status_tender"] or None,
                "order_timestamp": _parse_dt(row["order_timestamp"]),
                "tender_timestamp": _parse_dt(row["tender_timestamp"]),
                "driveraccept_timestamp": _parse_dt(row["driveraccept_timestamp"]),
                "driverarrived_timestamp": _parse_dt(row["driverarrived_timestamp"]),
                "driverstarttheride_timestamp": _parse_dt(row["driverstarttheride_timestamp"]),
                "driverdone_timestamp": _parse_dt(row["driverdone_timestamp"]),
                "clientcancel_timestamp": _parse_dt(row["clientcancel_timestamp"]),
                "drivercancel_timestamp": _parse_dt(row["drivercancel_timestamp"]),
                "order_modified_local": _parse_dt(row["order_modified_local"]),
                "cancel_before_accept_local": _parse_dt(row["cancel_before_accept_local"]),
                "distance_in_meters": float(row["distance_in_meters"]) if row["distance_in_meters"] else None,
                "duration_in_seconds": int(row["duration_in_seconds"]) if row["duration_in_seconds"] else None,
                "price_order_local": float(row["price_order_local"]) if row["price_order_local"] else None,
                "price_tender_local": float(row["price_tender_local"]) if row["price_tender_local"] else None,
                "price_start_local": float(row["price_start_local"]) if row["price_start_local"] else None,
            }
            batch.append(item)

            if len(batch) >= batch_size:
                await db.execute(insert(Trip), batch)
                await db.commit()
                inserted += len(batch)
                batch.clear()

    if batch:
        await db.execute(insert(Trip), batch)
        await db.commit()
        inserted += len(batch)

    return inserted


async def seed_database():
    """Seed auxiliary data and load trips from provided train.csv dataset."""
    from app.infrastructure.database import AsyncSessionLocal
    from app.infrastructure.models import City, Driver, Order, User, SemanticTerm
    from app.domain.entities import UserRole, OrderStatus
    from datetime import timedelta
    import random

    random.seed(42)

    async with AsyncSessionLocal() as db:
        city_count = await db.scalar(select(func.count(City.id))) or 0
        if city_count == 0:
            cities_data = [
                ("Москва", "Центральный", "2020-01-15"),
                ("Санкт-Петербург", "Северо-Западный", "2020-03-01"),
                ("Казань", "Приволжский", "2020-06-15"),
                ("Екатеринбург", "Уральский", "2021-01-10"),
                ("Краснодар", "Южный", "2021-04-20"),
                ("Нижний Новгород", "Приволжский", "2021-07-01"),
                ("Новосибирск", "Сибирский", "2022-02-14"),
                ("Ростов-на-Дону", "Южный", "2022-05-01"),
            ]
            for name, region, launch in cities_data:
                db.add(City(name=name, region=region, launch_date=datetime.fromisoformat(launch)))
            await db.commit()

        user_count = await db.scalar(select(func.count(User.id))) or 0
        if user_count == 0:
            users_data = [
                ("Анна Петрова", "anna@drivee.com", UserRole.ADMIN),
                ("Иван Смирнов", "ivan@drivee.com", UserRole.ANALYST),
                ("Мария Козлова", "maria@drivee.com", UserRole.MANAGER),
                ("Елена Соколова", "elena@drivee.com", UserRole.VIEWER),
            ]
            for name, email, role in users_data:
                db.add(User(name=name, email=email, role=role.value))
            await db.commit()

        driver_count = await db.scalar(select(func.count(Driver.id))) or 0
        if driver_count == 0:
            city_rows = (await db.execute(select(City))).scalars().all()
            for city in city_rows:
                for i in range(8):
                    db.add(Driver(
                        full_name=f"Driver {city.id}-{i+1}",
                        city_id=city.id,
                        rating=round(random.uniform(4.0, 5.0), 1),
                        total_trips=random.randint(50, 2000),
                        car_model=random.choice(["Toyota Camry", "Kia Rio", "Hyundai Solaris"]),
                        car_class=random.choice(["economy", "comfort", "business"]),
                        is_active=True,
                        joined_at=datetime.now() - timedelta(days=random.randint(90, 900)),
                    ))
            await db.commit()

        order_count = await db.scalar(select(func.count(Order.id))) or 0
        if order_count == 0:
            city_rows = (await db.execute(select(City))).scalars().all()
            for _ in range(500):
                city = random.choice(city_rows)
                status = random.choice([OrderStatus.COMPLETED.value, OrderStatus.CANCELLED.value])
                db.add(Order(
                    city_id=city.id,
                    status=status,
                    amount=round(random.uniform(120, 4500), 2),
                    channel=random.choice(["app", "web", "partner"]),
                    created_at=datetime.now() - timedelta(days=random.randint(0, 365)),
                    cancel_reason="Отмена пользователем" if status == OrderStatus.CANCELLED.value else None,
                ))
            await db.commit()

        semantic_count = await db.scalar(select(func.count(SemanticTerm.id))) or 0
        if semantic_count == 0:
            semantic_data = [
                ("выручка", ["доход", "revenue"], "SUM(trips.price_order_local)", "Суммарная стоимость заказов", "metric"),
                ("поездки", ["trips", "заказы"], "COUNT(DISTINCT trips.order_id)", "Количество заказов", "metric"),
                ("отмены", ["cancelled", "отмененные"], "COUNT(*) FILTER (WHERE trips.status_order = 'cancel')", "Количество отмен", "metric"),
                ("длительность", ["duration"], "AVG(trips.duration_in_seconds)", "Средняя длительность в секундах", "metric"),
                ("расстояние", ["distance"], "AVG(trips.distance_in_meters)", "Среднее расстояние в метрах", "metric"),
            ]
            for term, aliases, sql_expr, desc, cat in semantic_data:
                db.add(SemanticTerm(term=term, aliases=aliases, sql_expression=sql_expr, description=desc, category=cat))
            await db.commit()

        trip_count = await db.scalar(select(func.count(Trip.id))) or 0
        if trip_count == 0:
            csv_path = _find_train_csv_path()
            if csv_path:
                await _load_trips_from_csv(db, csv_path)
                await _sync_cities_from_trips(db)
        else:
            # Keep city dictionary aligned with anonymized trip city IDs.
            await _sync_cities_from_trips(db)


async def _sync_cities_from_trips(db) -> None:
    """Ensure every city_id present in trips exists in cities table."""
    from app.infrastructure.models import City

    trip_city_ids = (
        await db.execute(select(Trip.city_id).distinct().where(Trip.city_id.is_not(None)))
    ).scalars().all()
    if not trip_city_ids:
        return

    existing_city_ids = set((await db.execute(select(City.id))).scalars().all())
    missing = [cid for cid in trip_city_ids if cid not in existing_city_ids]
    if not missing:
        return

    for cid in missing:
        db.add(City(
            id=int(cid),
            name=f"Город {cid}",
            region="anonymized",
            is_active=True,
            launch_date=datetime(2020, 1, 1),
        ))
    await db.commit()


app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "driveery-api"}
