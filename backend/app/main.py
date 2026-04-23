from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.config import settings
from app.api.v1.router import router
from app.infrastructure.database import engine, Base

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
    await seed_database()


async def seed_database():
    """Seed comprehensive demo data for Drivee analytics platform."""
    from app.infrastructure.database import AsyncSessionLocal
    from app.infrastructure.models import City, Driver, Trip, Order, User, SemanticTerm
    from app.domain.entities import UserRole, TripStatus, OrderStatus
    from datetime import datetime, timedelta
    import random

    random.seed(42)

    async with AsyncSessionLocal() as db:
        city_count = await db.scalar(select(func.count(City.id)))
        if city_count and city_count > 0:
            return

        # ── Cities ──────────────────────────────────────────────────────────
        # revenue_multiplier: relative price level of city
        cities_data = [
            ("Москва",           "Центральный",       "2020-01-15", 1.8),
            ("Санкт-Петербург",  "Северо-Западный",   "2020-03-01", 1.4),
            ("Казань",           "Приволжский",       "2020-06-15", 0.9),
            ("Екатеринбург",     "Уральский",         "2021-01-10", 1.0),
            ("Краснодар",        "Южный",             "2021-04-20", 0.85),
            ("Нижний Новгород",  "Приволжский",       "2021-07-01", 0.80),
            ("Новосибирск",      "Сибирский",         "2022-02-14", 0.95),
            ("Ростов-на-Дону",   "Южный",             "2022-05-01", 0.75),
        ]
        cities = []
        city_mult: dict[str, float] = {}
        for name, region, launch, mult in cities_data:
            city = City(name=name, region=region, launch_date=datetime.fromisoformat(launch))
            db.add(city)
            cities.append(city)
            city_mult[name] = mult
        await db.flush()

        # ── Drivers ─────────────────────────────────────────────────────────
        first_names = [
            "Александр", "Дмитрий", "Сергей", "Андрей", "Максим",
            "Иван", "Алексей", "Владимир", "Роман", "Николай",
            "Антон", "Михаил", "Артём", "Олег", "Евгений",
            "Виктор", "Павел", "Станислав", "Кирилл", "Тимур",
        ]
        last_names = [
            "Иванов", "Смирнов", "Козлов", "Новиков", "Морозов",
            "Петров", "Волков", "Соколов", "Попов", "Лебедев",
            "Кузнецов", "Семёнов", "Орлов", "Захаров", "Медведев",
            "Фёдоров", "Егоров", "Павлов", "Степанов", "Тихонов",
        ]
        car_pool = [
            ("Toyota Camry",       "comfort"),
            ("Hyundai Solaris",    "economy"),
            ("Kia Rio",            "economy"),
            ("VW Polo",            "economy"),
            ("Lada Vesta",         "economy"),
            ("Lada Granta",        "economy"),
            ("Skoda Octavia",      "comfort"),
            ("Toyota Corolla",     "comfort"),
            ("Kia Optima",         "comfort"),
            ("Hyundai Sonata",     "comfort"),
            ("BMW 5 Series",       "business"),
            ("Mercedes E-Class",   "business"),
            ("Audi A6",            "business"),
        ]
        drivers_per_city = {
            "Москва": 40, "Санкт-Петербург": 30, "Казань": 20,
            "Екатеринбург": 22, "Краснодар": 16, "Нижний Новгород": 15,
            "Новосибирск": 18, "Ростов-на-Дону": 13,
        }

        all_drivers: list[tuple] = []  # (Driver ORM object, City ORM object)
        for city in cities:
            count = drivers_per_city.get(city.name, 15)
            for _ in range(count):
                car_model, car_class = random.choice(car_pool)
                driver = Driver(
                    full_name=f"{random.choice(last_names)} {random.choice(first_names)}",
                    city_id=city.id,
                    rating=round(min(5.0, max(3.2, random.gauss(4.45, 0.38))), 1),
                    total_trips=random.randint(15, 2200),
                    car_model=car_model,
                    car_class=car_class,
                    is_active=random.random() > 0.12,
                    joined_at=datetime.now() - timedelta(days=random.randint(60, 1200)),
                )
                db.add(driver)
                all_drivers.append((driver, city))
        await db.flush()

        # ── Trips (5 000, 12 months, realistic patterns) ─────────────────────
        cancel_reasons = [
            "Долгое ожидание водителя",
            "Водитель не приехал к месту",
            "Изменились планы пассажира",
            "Не устроила цена",
            "Нашёл другой транспорт",
            "Технический сбой приложения",
            "Нет доступных водителей поблизости",
        ]
        # Rush-hour weights: peak at 8, 18, 20 hrs
        hours_weights = [1, 1, 1, 1, 2, 3, 5, 8, 9, 6, 5, 5, 6, 5, 5, 6, 7, 9, 10, 9, 7, 5, 3, 2]

        now = datetime.now()
        for _ in range(5000):
            driver, city = random.choice(all_drivers)
            days_ago = random.randint(0, 365)
            hour = random.choices(range(24), weights=hours_weights)[0]
            ts = now - timedelta(days=days_ago, hours=hour, minutes=random.randint(0, 59))

            # Seasonal factor
            m = ts.month
            season = 1.15 if m in (6, 7, 8) else (0.88 if m in (12, 1, 2) else 1.0)

            mult = city_mult.get(city.name, 1.0)

            # Cancel rate: lower in big cities (better supply)
            cancel_rate = {
                "Москва": 0.13, "Санкт-Петербург": 0.16,
            }.get(city.name, 0.21)

            status = random.choices(
                [TripStatus.COMPLETED, TripStatus.CANCELLED],
                weights=[1 - cancel_rate, cancel_rate],
            )[0]

            distance = round(random.uniform(1.2, 48.0), 1)
            duration = int(distance * random.uniform(2.0, 5.5))

            trip = Trip(
                driver_id=driver.id,
                city_id=city.id,
                status=status.value,
                distance_km=distance,
                duration_min=min(duration, 130),
                revenue=round(random.uniform(160, 3200) * mult * season, 2),
                passenger_rating=(
                    round(min(5.0, max(1.0, random.gauss(4.35, 0.55))), 1)
                    if status == TripStatus.COMPLETED else None
                ),
                started_at=ts,
                ended_at=ts + timedelta(minutes=duration) if status == TripStatus.COMPLETED else None,
                cancel_reason=random.choice(cancel_reasons) if status == TripStatus.CANCELLED else None,
            )
            db.add(trip)

        # ── Orders (2 000) ───────────────────────────────────────────────────
        order_cancel_reasons = [
            "Отменён пользователем",
            "Нет доступных водителей",
            "Истёк таймаут ожидания",
            "Платёжная ошибка",
            "Дубликат заказа",
        ]
        channels = ["app", "app", "app", "app", "web", "web", "partner"]

        for _ in range(2000):
            city = random.choice(cities)
            days_ago = random.randint(0, 365)
            ts = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            status = random.choices(
                [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
                weights=[0.85, 0.15],
            )[0]
            order = Order(
                city_id=city.id,
                status=status.value,
                amount=round(random.uniform(170, 3800) * city_mult.get(city.name, 1.0), 2),
                channel=random.choice(channels),
                created_at=ts,
                cancel_reason=random.choice(order_cancel_reasons) if status == OrderStatus.CANCELLED else None,
            )
            db.add(order)

        # ── Platform users ───────────────────────────────────────────────────
        users_data = [
            ("Анна Петрова",    "anna@drivee.com",   UserRole.ADMIN),
            ("Иван Смирнов",    "ivan@drivee.com",   UserRole.ANALYST),
            ("Мария Козлова",   "maria@drivee.com",  UserRole.MANAGER),
            ("Дмитрий Новиков", "dima@drivee.com",   UserRole.MANAGER),
            ("Елена Соколова",  "elena@drivee.com",  UserRole.VIEWER),
            ("Павел Орлов",     "pavel@drivee.com",  UserRole.ANALYST),
            ("Ольга Захарова",  "olga@drivee.com",   UserRole.MANAGER),
        ]
        for name, email, role in users_data:
            db.add(User(name=name, email=email, role=role.value))

        # ── Semantic layer ───────────────────────────────────────────────────
        semantic_data = [
            ("выручка",
             ["доход", "revenue", "деньги", "заработок", "прибыль"],
             "SUM(trips.revenue)",
             "Суммарная выручка по завершённым поездкам в рублях", "metric"),
            ("поездки",
             ["trips", "заказы", "рейсы", "поездка"],
             "COUNT(trips.id)",
             "Общее количество поездок всех статусов", "metric"),
            ("отмены",
             ["cancelled", "отменённые", "отменённые поездки", "отказы", "отмена"],
             "COUNT(trips.id) FILTER (WHERE trips.status = 'cancelled')",
             "Количество отменённых поездок", "metric"),
            ("активные водители",
             ["active drivers", "работающие водители"],
             "COUNT(DISTINCT drivers.id) FILTER (WHERE drivers.is_active = true)",
             "Число водителей с активным статусом", "metric"),
            ("рейтинг",
             ["rating", "оценка", "звёзды", "средний рейтинг"],
             "AVG(drivers.rating)",
             "Средний рейтинг водителей (шкала 1–5)", "metric"),
            ("средний чек",
             ["average revenue", "avg revenue", "средняя выручка"],
             "AVG(trips.revenue)",
             "Средняя выручка на одну поездку", "metric"),
            ("конверсия",
             ["conversion rate", "процент завершённых"],
             "ROUND(100.0 * SUM(CASE WHEN trips.status='completed' THEN 1 ELSE 0 END) / COUNT(*), 2)",
             "Доля завершённых поездок в % от всех", "metric"),
            ("города",
             ["cities", "регионы", "локации", "город"],
             "cities.name",
             "Разрез данных по городу присутствия Drivee", "dimension"),
            ("класс авто",
             ["car_class", "тариф", "категория авто", "economy", "comfort", "business"],
             "drivers.car_class",
             "Класс автомобиля водителя: economy / comfort / business", "dimension"),
            ("канал",
             ["channel", "источник заказа", "app", "web", "partner"],
             "orders.channel",
             "Канал, через который поступил заказ", "dimension"),
            ("Питер",
             ["Спб", "СПБ", "спб", "питер", "saint petersburg", "ленинград"],
             "'Санкт-Петербург'",
             "Псевдоним города Санкт-Петербург", "alias"),
            ("Мск",
             ["мск", "МСК", "Москва", "moscow"],
             "'Москва'",
             "Псевдоним города Москва", "alias"),
            ("неделя",
             ["week", "недельный", "7 дней", "за неделю"],
             "INTERVAL '7 days'",
             "Временной интервал — последние 7 дней", "filter"),
            ("месяц",
             ["month", "месячный", "30 дней", "за месяц"],
             "INTERVAL '30 days'",
             "Временной интервал — последние 30 дней", "filter"),
            ("квартал",
             ["quarter", "квартальный", "90 дней", "за квартал"],
             "INTERVAL '90 days'",
             "Временной интервал — последние 90 дней", "filter"),
        ]
        for term, aliases, sql_expr, desc, cat in semantic_data:
            db.add(SemanticTerm(
                term=term, aliases=aliases,
                sql_expression=sql_expr, description=desc, category=cat,
            ))

        await db.commit()


app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "driveery-api"}
