from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centraliza la configuración para que la app sea desplegable como SaaS."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    env: str = Field("development", validation_alias="ENV")
    app_name: str = Field("SaaS Reporting AI", validation_alias="APP_NAME")

    # Seguridad
    secret_key: str = Field("change-me", validation_alias="SECRET_KEY")
    algorithm: str = Field("HS256", validation_alias="ALGORITHM")
    access_token_expire_minutes: int = Field(60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Base de datos / cache
    database_url: str = Field("sqlite:///./saas_v1.db", validation_alias="DATABASE_URL")
    redis_url: Optional[str] = Field(default=None, validation_alias="REDIS_URL")

    # Red / frontend
    cors_origins: List[str] = Field(default_factory=lambda: ["*"], validation_alias="CORS_ORIGINS")
    trusted_hosts: List[str] = Field(default_factory=list, validation_alias="TRUSTED_HOSTS")

    # Rate limiting multi-tenant
    rate_limit: int = Field(50, validation_alias="RATE_LIMIT")
    rate_limit_period: int = Field(60, validation_alias="RATE_LIMIT_PERIOD")

    fernet_key: Optional[str] = Field(default=None, validation_alias="FERNET_KEY")

    # AI
    ai_provider: str = Field("cheap_api", validation_alias="AI_PROVIDER")
    ai_api_url: str = Field("", validation_alias="AI_API_URL")
    ai_api_key: str = Field("", validation_alias="AI_API_KEY")
    ai_timeout: float = Field(8.0, validation_alias="AI_TIMEOUT")
    ai_max_concurrency: int = Field(4, validation_alias="AI_MAX_CONCURRENCY")
    cost_per_1k_tokens: float = Field(0.4, validation_alias="COST_PER_1K_TOKENS")

    chunk_size: int = Field(1000, validation_alias="CHUNK_SIZE")

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg2://", 1)
        return value

    @field_validator("cors_origins", "trusted_hosts", mode="before")
    @classmethod
    def split_csv(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()

    if settings.env == "production" and settings.secret_key == "change-me":
        raise RuntimeError("SECRET_KEY must be set for production deployments")

    return settings
