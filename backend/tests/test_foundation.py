from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=SecretStr("postgresql+psycopg://test:test@localhost/test"),
        redis_url=SecretStr("redis://localhost:6379/15"),
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings), raise_server_exceptions=False) as client:
        yield client


def test_health_and_versioned_status(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "kagex-api",
        "version": "0.1.0",
    }
    assert client.get("/api/v1/status").json() == {
        "phase": "foundation",
        "analysis_available": False,
    }


@pytest.mark.parametrize(
    "postgres_ok,redis_ok", [(True, True), (False, True), (True, False), (False, False)]
)
def test_readiness(settings: Settings, postgres_ok: bool, redis_ok: bool) -> None:
    app = create_app(settings)
    with TestClient(app) as client:
        engine, redis = MagicMock(), MagicMock()
        if not postgres_ok:
            engine.connect.side_effect = OperationalError(
                "SELECT 1", {}, Exception("secret")
            )
        if not redis_ok:
            redis.ping.side_effect = RedisConnectionError("secret")
        else:
            redis.ping.return_value = True
        app.state.engine, app.state.redis = engine, redis
        response = client.get("/ready")
        assert response.status_code == (200 if postgres_ok and redis_ok else 503)
        assert response.json() == {
            "status": "ready" if postgres_ok and redis_ok else "unavailable",
            "postgres": postgres_ok,
            "redis": redis_ok,
        }
        assert "secret" not in response.text
        assert client.get("/health").status_code == 200


def test_cors_and_not_found(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    response = client.get("/health", headers={"Origin": "https://untrusted.example"})
    assert "access-control-allow-origin" not in response.headers
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "HTTP_ERROR"


def test_configuration_validation(settings: Settings) -> None:
    values = settings.model_dump()
    with pytest.raises(ValidationError):
        Settings(**{**values, "cors_allowed_origins": ["*"]})
    with pytest.raises(ValidationError):
        Settings(**{**values, "backend_port": 70000})
    with pytest.raises(ValidationError):
        Settings(**{**values, "database_url": "sqlite:///test.db"})
    assert "test:test" not in repr(settings)


def test_environment_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://test:test@localhost/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("BACKEND_PORT", "8010")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", '["https://kagex.example"]')
    settings = Settings(_env_file=None)
    assert settings.backend_port == 8010
    assert settings.cors_allowed_origins == ["https://kagex.example"]


def test_safe_errors(settings: Settings, caplog: pytest.LogCaptureFixture) -> None:
    app = create_app(settings)

    @app.get("/test-error")
    def broken() -> None:
        raise RuntimeError("sensitive-value")

    @app.get("/test-validation")
    def validated(number: int) -> int:
        return number

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-error")
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_ERROR"
        assert "sensitive-value" not in response.text + caplog.text
        response = client.get("/test-validation?number=sensitive-value")
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "sensitive-value" not in response.text
