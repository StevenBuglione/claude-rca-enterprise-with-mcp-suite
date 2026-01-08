from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8080, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    base_url: str = Field(alias="CONFLUENCE_BASE_URL")
    api_prefix: str = Field(default="/rest/api", alias="CONFLUENCE_API_PREFIX")

    auth_mode: str = Field(default="bearer", alias="CONFLUENCE_AUTH_MODE")  # bearer|basic
    user: str = Field(default="", alias="CONFLUENCE_USER")
    token: str = Field(alias="CONFLUENCE_TOKEN")
    verify_ssl: bool = Field(default=True, alias="CONFLUENCE_VERIFY_SSL")

settings = Settings()  # type: ignore[call-arg]
