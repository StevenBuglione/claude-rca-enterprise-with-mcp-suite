from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl, Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    port: int = Field(default=8000)

    # Concurrency
    max_concurrent_rca: int = Field(default=2, ge=1)

    # Evidence store
    evidence_store_url: str = Field(default="postgresql://rca:rca@postgres:5432/rca")

    # Logging
    log_level: str = Field(default="INFO")

    # OTel
    otel_service_name: str = Field(default="claude-rca-api")


settings = Settings()
