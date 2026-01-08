from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8080, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    base_url: str = Field(alias="BITBUCKET_BASE_URL")
    api_prefix: str = Field(default="/rest/api/1.0", alias="BITBUCKET_API_PREFIX")

    auth_mode: str = Field(default="bearer", alias="BITBUCKET_AUTH_MODE")  # bearer|basic
    user: str = Field(default="", alias="BITBUCKET_USER")
    token: str = Field(alias="BITBUCKET_TOKEN")
    verify_ssl: bool = Field(default=True, alias="BITBUCKET_VERIFY_SSL")

settings = Settings()  # type: ignore[call-arg]
