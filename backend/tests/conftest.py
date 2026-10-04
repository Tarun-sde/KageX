import os
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import Engine, create_engine, text

from alembic import command
from app.core.config import Settings
from app.main import create_app

HEADERS = {"Origin": "http://localhost:5173", "X-KageX-Request": "1"}
PASSWORD = "correct horse battery staple"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=SecretStr(
            os.environ.get(
                "TEST_DATABASE_URL",
                "postgresql+psycopg://kagex:kagex_dev_only@localhost:5432/kagex",
            )
        ),
        redis_url=SecretStr("redis://localhost:6379/15"),
        project_storage_root=tmp_path / "sources",
        max_upload_size_mb=1,
        max_file_size_mb=1,
        max_extracted_size_mb=2,
        max_archive_files=10,
    )


@pytest.fixture
def engine(settings: Settings) -> Iterator[Engine]:
    # Real PostgreSQL, migrations, and independent request transactions. Never
    # truncate shared tables: each test owns a randomly named disposable schema.
    schema = "test_" + uuid4().hex
    admin = create_engine(settings.database_url.get_secret_value())
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    isolated = create_engine(
        settings.database_url.get_secret_value(),
        connect_args={"options": f"-c search_path={schema}"},
    )
    try:
        config = Config("alembic.ini")
        with isolated.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield isolated
    finally:
        isolated.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture
def client(settings: Settings, engine: Engine) -> Iterator[TestClient]:
    app = create_app(settings)
    with TestClient(app) as client:
        app.state.engine = engine
        client.headers.update(HEADERS)
        yield client


def register(client: TestClient, email: str = "alice@example.com") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


def project(client: TestClient, source: str = "ZIP_UPLOAD") -> str:
    response = client.post(
        "/api/v1/projects", json={"name": "Test project", "source_type": source}
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])
