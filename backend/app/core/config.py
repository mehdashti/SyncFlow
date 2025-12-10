"""
Core Configuration Module

Uses Pydantic Settings for type-safe configuration management.
"""

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8008
    API_PREFIX: str = "/api/v1"

    # Database (SyncFlow Metadata)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "bridge_v2_db"
    POSTGRES_SCHEMA: str = "bridge"
    POSTGRES_USER: str = "bridge_user"
    POSTGRES_PASSWORD: str = "bridge_password"
    POSTGRES_POOL_SIZE: int = 20

    @property
    def DATABASE_URL(self) -> str:
        """Construct async PostgreSQL URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # APISmith
    APISmith_URL: str = "http://localhost:8007"
    APISmith_TOKEN: str = ""

    # ScheduleHub
    ScheduleHub_URL: str = "http://localhost:5180"
    ScheduleHub_TOKEN: str = ""

    # Sync Configuration
    DEFAULT_BATCH_SIZE: int = 1000
    MAX_BATCH_SIZE: int = 10000
    DEFAULT_SYNC_INTERVAL_SECONDS: int = 300
    SYNC_WORKER_THREADS: int = 4

    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 60
    MAX_RETRY_DELAY_SECONDS: int = 3600

    # Background Sync
    BACKGROUND_SYNC_ENABLED: bool = True
    BACKGROUND_SYNC_WINDOW_START: str = "19:00:00"
    BACKGROUND_SYNC_WINDOW_END: str = "07:00:00"

    # Security
    INTERNAL_SERVICE_JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging
    LOG_FILE: str = "/var/log/bridge_v2.log"
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 5

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @computed_field
    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins to list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
