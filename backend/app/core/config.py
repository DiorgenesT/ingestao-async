from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    DATABASE_URL: str

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def garantir_asyncpg(cls, v: str) -> str:
        if v.startswith("postgresql://") or v.startswith("postgres://"):
            return v.replace("://", "+asyncpg://", 1)
        return v
    TEST_DATABASE_URL: str = ""
    SECRET_KEY: str
    ENVIRONMENT: str = "development"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    JOB_MAX_TENTATIVAS: int = 3
    JOB_VISIBILITY_TIMEOUT_SEGUNDOS: int = 300
    JOB_BACKOFF_BASE_SEGUNDOS: int = 60

    WORKER_POLL_INTERVAL_SEGUNDOS: int = 5
    WORKER_BATCH_SIZE: int = 10

    CORS_ORIGINS: str = "http://localhost:5173"

    RATE_LIMIT_POR_MINUTO: int = 60
    UPLOAD_MAX_BYTES: int = 50 * 1024 * 1024  # 50 MB
    UPLOAD_DIR: str = "/tmp/ingestao-async-uploads"

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
