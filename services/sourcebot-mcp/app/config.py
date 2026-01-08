from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8080, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    mode: str = Field(default="mock", alias="SOURCEBOT_MODE")  # mock|proxy
    mock_data_path: str = Field(
        default=str(Path(__file__).resolve().parent / "mock_data.json"),
        alias="SOURCEBOT_MOCK_DATA",
    )

    sourcebot_host: str = Field(default="", alias="SOURCEBOT_HOST")
    api_key: str = Field(default="", alias="SOURCEBOT_API_KEY")
    verify_ssl: bool = Field(default=True, alias="SOURCEBOT_VERIFY_SSL")


settings = Settings()
