from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8080, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    base_url: str = Field(alias="JENKINS_BASE_URL")
    user: str = Field(alias="JENKINS_USER")
    api_token: str = Field(alias="JENKINS_API_TOKEN")
    verify_ssl: bool = Field(default=True, alias="JENKINS_VERIFY_SSL")

settings = Settings()  # type: ignore[call-arg]
