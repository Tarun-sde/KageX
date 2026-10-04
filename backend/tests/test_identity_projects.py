from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, inspect, select
from sqlalchemy.orm import Session

from alembic import command
from app.api.auth import password_hasher
from app.core.config import Settings
from app.core.security import cookie_name, token_hash
from app.models import AuthSession, Project, User, now
from tests.conftest import HEADERS, PASSWORD, project, register


def test_auth_lifecycle(client: TestClient, engine: Engine) -> None:
    user = register(client, "Alice@EXAMPLE.com")
    assert set(user) == {"id", "email"}
    assert user["email"] == "alice@example.com"
    token = client.cookies["kagex_session"]
    with Session(engine) as db:
        stored = db.scalar(select(User))
        assert stored and stored.password_hash.startswith("$argon2id$")
        assert password_hasher.verify(stored.password_hash, PASSWORD)
        assert db.get(AuthSession, token_hash(token)) is not None
        assert db.get(AuthSession, token) is None
    assert client.get("/api/v1/auth/me").json() == user
    assert (
        client.post(
            "/api/v1/auth/register", json={"email": user["email"], "password": PASSWORD}
        ).status_code
        == 409
    )
    for email in (user["email"], "unknown@example.com"):
        bad = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrong password value"},
        )
        assert bad.status_code == 401
        assert bad.json()["error"]["code"] == "INVALID_CREDENTIALS"
    login = client.post(
        "/api/v1/auth/login", json={"email": user["email"], "password": PASSWORD}
    )
    assert login.status_code == 200
    assert "HttpOnly" in login.headers["set-cookie"]
    assert "SameSite=lax" in login.headers["set-cookie"]
    assert "no-store" in login.headers["cache-control"]
    renewed = client.cookies["kagex_session"]
    assert renewed != token
    with Session(engine) as db:
        assert db.get(AuthSession, token_hash(token)) is None
    assert client.post("/api/v1/auth/logout").status_code == 204
    client.cookies.set("kagex_session", renewed)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_expired_inactive_and_invalid_sessions(
    client: TestClient, engine: Engine
) -> None:
    register(client)
    token = client.cookies["kagex_session"]
    with Session(engine) as db:
        session = db.get(AuthSession, token_hash(token))
        assert session
        session.expires_at = now() - timedelta(seconds=1)
        db.commit()
    assert client.get("/api/v1/auth/me").status_code == 401
    client.post(
        "/api/v1/auth/login", json={"email": "alice@example.com", "password": PASSWORD}
    )
    with Session(engine) as db:
        user = db.scalar(select(User))
        assert user
        user.is_active = False
        db.commit()
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.clear()
    client.cookies.set("kagex_session", "forged")
    assert client.get("/api/v1/projects").status_code == 401


@pytest.mark.parametrize(
    "body",
    [
        {"email": "bad", "password": PASSWORD},
        {"email": "a@example.com", "password": "short"},
        {"email": "a@example.com", "password": "a" * 129},
        {"email": "a@example.com", "password": PASSWORD, "is_active": True},
    ],
)
def test_credentials_validation(client: TestClient, body: dict[str, object]) -> None:
    response = client.post("/api/v1/auth/register", json=body)
    assert response.status_code == 422
    assert PASSWORD not in response.text


def test_csrf_cors_and_body_limits(client: TestClient) -> None:
    for headers in (
        {},
        {"Origin": "https://evil.example", "X-KageX-Request": "1"},
        {"Origin": HEADERS["Origin"]},
    ):
        client.headers.clear()
        response = client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 403
    client.headers.update(HEADERS)
    assert (
        client.post(
            "/api/v1/auth/register", content='{"email":"' + "x" * 17000
        ).status_code
        == 413
    )
    preflight = client.options(
        "/api/v1/projects",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in preflight.headers
    good = client.options(
        "/api/v1/projects",
        headers={
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-KageX-Request",
        },
    )
    assert good.status_code == 200
    assert good.headers["access-control-allow-origin"] == HEADERS["Origin"]


def test_ownership_all_routes_and_crud(client: TestClient, engine: Engine) -> None:
    assert client.get("/api/v1/projects").status_code == 401
    alice = register(client)
    identifier = project(client)
    base = f"/api/v1/projects/{identifier}"
    assert client.patch(base, json={"name": "Renamed"}).json()["name"] == "Renamed"
    for field in ("owner_id", "status", "github_url"):
        assert (
            client.patch(base, json={"name": "Test", field: alice["id"]}).status_code
            == 422
        )
    assert (
        client.post(
            "/api/v1/projects", json={"name": " ", "source_type": "ZIP_UPLOAD"}
        ).status_code
        == 422
    )
    register(client, "bob@example.com")
    assert client.get("/api/v1/projects").json() == []
    for path in (base, f"/api/v1/projects/{uuid4()}"):
        assert client.get(path).status_code == 404
        assert client.patch(path, json={"name": "Stolen"}).status_code == 404
        assert client.delete(path).status_code == 404
        assert client.post(path + "/source/zip", content=b"bad").status_code == 404
        assert (
            client.post(
                path + "/source/github", json={"url": "https://github.com/a/b"}
            ).status_code
            == 404
        )
    with Session(engine) as db:
        stored = db.get(Project, UUID(identifier))
        assert stored and str(stored.owner_id) == alice["id"]
    client.post(
        "/api/v1/auth/login", json={"email": alice["email"], "password": PASSWORD}
    )
    assert len(client.get("/api/v1/projects").json()) == 1
    assert client.delete(base).status_code == 204
    assert client.get(base).status_code == 404


def test_project_lock_conflict(client: TestClient, engine: Engine) -> None:
    register(client)
    identifier = project(client)
    with Session(engine) as db:
        db.scalar(
            select(Project).where(Project.id == UUID(identifier)).with_for_update()
        )
        assert client.delete(f"/api/v1/projects/{identifier}").status_code == 409
        assert (
            client.patch(
                f"/api/v1/projects/{identifier}", json={"name": "Busy"}
            ).json()["error"]["code"]
            == "PROJECT_BUSY"
        )
    assert client.delete(f"/api/v1/projects/{identifier}").status_code == 204


def test_migration_roundtrip(engine: Engine) -> None:
    config = Config("alembic.ini")
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.check(config)
        command.downgrade(config, "base")
        assert inspect(connection).get_table_names() == ["alembic_version"]
        command.upgrade(config, "head")
        command.check(config)
        assert set(inspect(connection).get_table_names()) == {
            "alembic_version",
            "users",
            "auth_sessions",
            "projects",
        }


def test_production_cookie_settings(settings: Settings) -> None:
    production = settings.model_copy(update={"app_env": "production"})
    assert cookie_name(production) == "__Host-kagex_session"


def test_production_cookie_and_logs(
    client: TestClient, settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    import httpx2

    settings.app_env = "production"
    settings.cors_allowed_origins = ["https://kagex.example"]
    client.base_url = httpx2.URL("https://kagex.example")
    client.headers["Origin"] = "https://kagex.example"
    with caplog.at_level("INFO"):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "prod@example.com", "password": PASSWORD},
        )
    assert response.status_code == 201
    cookie = response.headers["set-cookie"]
    assert "__Host-kagex_session=" in cookie
    assert "Secure" in cookie and "HttpOnly" in cookie and "Path=/" in cookie
    assert "Domain=" not in cookie
    assert client.get("/api/v1/auth/me").status_code == 200
    assert PASSWORD not in caplog.text
    assert client.cookies["__Host-kagex_session"] not in caplog.text
    assert "password_hash" not in response.text
