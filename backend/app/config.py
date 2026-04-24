from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # PostgreSQL in Docker, SQLite for local dev fallback
    DATABASE_URL: str = "postgresql+asyncpg://driveery:driveery@db:5432/driveery"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "qwen/qwen3.6-plus"
    TRAIN_CSV_PATH: str = "train.csv"
    SECRET_KEY: str = "supersecretkey"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
