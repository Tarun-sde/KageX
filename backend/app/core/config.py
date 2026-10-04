from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, ValidationInfo, field_validator, model_validator
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

    session_ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    project_storage_root: Path = (
        Path(__file__).resolve().parents[3] / ".data" / "sources"
    )
    max_upload_size_mb: int = Field(default=25, ge=1, le=100)
    max_extracted_size_mb: int = Field(default=100, ge=1, le=1000)
    max_archive_files: int = Field(default=2000, ge=1, le=10000)
    max_file_size_mb: int = Field(default=10, ge=1, le=100)
    max_compression_ratio: int = Field(default=100, ge=1, le=1000)
    ingestion_timeout_seconds: int = Field(default=30, ge=1, le=120)

    @model_validator(mode="after")
    def production_safety(self) -> Settings:
        if self.app_env == "production" and (
            not self.frontend_url.startswith("https://")
            or not self.cors_allowed_origins
            or any(
                not origin.startswith("https://")
                for origin in self.cors_allowed_origins
            )
        ):
            raise ValueError(
                "Production authentication requires explicit HTTPS origins"
            )
        if (
            not self.project_storage_root.is_absolute()
            or self.project_storage_root == Path("/")
        ):
            raise ValueError("Storage requires a dedicated absolute directory")
        return self

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
