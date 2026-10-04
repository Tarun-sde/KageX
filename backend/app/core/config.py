from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_env: Literal["development", "test", "production"] = "development"
    backend_host: str = "127.0.0.1"
    backend_port: int = Field(default=8000, ge=1, le=65535)
    frontend_url: str = "http://localhost:5173"
    cors_allowed_origins: list[str] = ["http://localhost:5173"]
    database_url: SecretStr
    redis_url: SecretStr
    celery_broker_url: SecretStr = SecretStr("")
    celery_result_backend: SecretStr = SecretStr("")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("frontend_url")
    @classmethod
    def validate_origin(cls, value: str) -> str:
        url = urlsplit(value)
        if (
            url.scheme not in {"http", "https"}
            or not url.netloc
            or url.username
            or url.password
            or url.path not in {"", "/"}
            or url.query
            or url.fragment
        ):
            raise ValueError("Expected an explicit HTTP(S) origin")
        return value.rstrip("/")

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_origins(cls, values: list[str]) -> list[str]:
        return [cls.validate_origin(value) for value in values]

    @field_validator("database_url")
    @classmethod
    def validate_database(cls, value: SecretStr) -> SecretStr:
        if urlsplit(value.get_secret_value()).scheme != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use postgresql+psycopg")
        return value

    @field_validator("redis_url", "celery_broker_url", "celery_result_backend")
    @classmethod
    def validate_redis(cls, value: SecretStr, info: ValidationInfo) -> SecretStr:
        raw = value.get_secret_value()
        if (not raw and info.field_name == "redis_url") or (
            raw
            and (
                urlsplit(raw).scheme not in {"redis", "rediss"}
                or not urlsplit(raw).hostname
            )
        ):
            raise ValueError("Expected a redis:// or rediss:// URL")
        return value
