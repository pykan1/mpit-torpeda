from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router
from app.infrastructure.database import Base, engine

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
    # Schema is created/updated by SQLAlchemy, data bootstrap is handled by
    # Postgres init scripts (db/init/*.sql.gz) on first empty database start.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "driveery-api"}
