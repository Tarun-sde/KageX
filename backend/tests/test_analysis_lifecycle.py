from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select, text
from sqlalchemy.orm import Session

from alembic import command
from app.analyzers.contracts import AnalysisFailure
from app.core.config import Settings
from app.models import now
from app.models.analysis import AnalysisEntity, AnalysisRun, RunStatus
from app.services.analysis import execute_analysis
from tests.conftest import PASSWORD, project, register
from tests.test_analyzers import FIXTURES
from tests.test_ingestion import archive


@pytest.fixture
def queue(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> Mock:
    queue = Mock()
    monkeypatch.setattr(client.app.state.celery, "send_task", queue)  # type: ignore[attr-defined]
    return queue


def ready(client: TestClient, entries: list[tuple[str, bytes]] | None = None) -> str:
    identifier = project(client)
    response = client.post(
        f"/api/v1/projects/{identifier}/source/zip",
        content=archive(
            entries
            or [("main.py", b"def choose(x):\n    if x: return 1\n    return 0\n")]
        ),
    )
    assert response.status_code == 200, response.text
    return identifier


def start(client: TestClient, identifier: str) -> UUID:
    response = client.post(f"/api/v1/projects/{identifier}/analyses")
    assert response.status_code == 202, response.text
    return UUID(response.json()["id"])


def test_lifecycle_real_parser_and_idempotency(
    client: TestClient, queue: Mock, engine: Engine, settings: Settings
) -> None:
    register(client)
    identifier = ready(client)
    base = f"/api/v1/projects/{identifier}/analyses"
    run_id = start(client, identifier)
    queue.assert_called_once()
    with Session(engine) as db:
        assert db.get(AnalysisRun, run_id).status == RunStatus.QUEUED  # type: ignore[union-attr]
    assert client.post(base).status_code == 409
    assert client.delete(f"/api/v1/projects/{identifier}").status_code == 409
    execute_analysis(run_id, engine, settings)
    result = client.get(f"{base}/{run_id}").json()
    assert result["status"] == "COMPLETED", result
    assert result["summary"]["entities_analyzed"] == 1
    assert result["summary"]["supported_files"] == 1
    assert str(settings.project_storage_root) not in str(result)
    entities = client.get(f"{base}/{run_id}/entities?limit=1").json()
    assert entities["items"][0]["metrics"]["cyclomatic_complexity"] == 2
    assert entities["total"] == 1
    assert client.get(f"{base}/{run_id}/entities?offset=1").json()["items"] == []
    assert client.get(f"{base}/{run_id}/entities?language=java").json()["total"] == 0
    assert client.get(f"{base}/{run_id}/entities?limit=101").status_code == 422
    execute_analysis(run_id, engine, settings)
    assert client.get(f"{base}/{run_id}").json() == result
    assert client.get(f"{base}/{run_id}/entities").json()["items"] == entities["items"]
    second = start(client, identifier)
    execute_analysis(second, engine, settings)
    assert len(client.get(base).json()) == 2
    assert client.delete(f"/api/v1/projects/{identifier}").status_code == 204
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(AnalysisEntity)) == 0


def test_analysis_ownership_and_not_ready(
    client: TestClient, queue: Mock, engine: Engine, settings: Settings
) -> None:
    assert client.get(f"/api/v1/projects/{uuid4()}/analyses").status_code == 401
    alice = register(client)
    empty = project(client)
    assert (
        client.post(f"/api/v1/projects/{empty}/analyses").json()["error"]["code"]
        == "PROJECT_NOT_READY"
    )
    identifier = ready(client)
    run_id = start(client, identifier)
    execute_analysis(run_id, engine, settings)
    register(client, "other@example.com")
    own = ready(client)
    for target in (identifier, str(uuid4())):
        base = f"/api/v1/projects/{target}/analyses"
        assert client.post(base).status_code == 404
        assert client.get(base).status_code == 404
        assert client.get(f"{base}/{run_id}").status_code == 404
        assert client.get(f"{base}/{run_id}/entities").status_code == 404
    assert (
        client.get(f"/api/v1/projects/{own}/analyses/{run_id}/entities").status_code
        == 404
    )
    client.post(
        "/api/v1/auth/login", json={"email": alice["email"], "password": PASSWORD}
    )
    assert (
        client.get(f"/api/v1/projects/{identifier}/analyses/{run_id}").status_code
        == 200
    )


def test_queue_failure_after_commit(
    client: TestClient, queue: Mock, engine: Engine
) -> None:
    register(client)
    identifier = ready(client)

    def fail(*args: object, **kwargs: object) -> None:
        with Session(engine) as db:
            assert db.scalar(select(AnalysisRun)) is not None
        raise RuntimeError("secret broker password")

    queue.side_effect = fail
    response = client.post(f"/api/v1/projects/{identifier}/analyses")
    assert response.status_code == 503
    assert "secret" not in response.text
    result = client.get(f"/api/v1/projects/{identifier}/analyses").json()[0]
    assert result["status"] == "FAILED"
    assert result["error_code"] == "QUEUE_UNAVAILABLE"


@pytest.mark.parametrize(
    "entries,code",
    [
        ([("README.md", b"text")], "NO_SUPPORTED_SOURCE"),
        ([("broken.py", b"def (")], "NO_ANALYZABLE_ENTITIES"),
    ],
)
def test_no_source_or_all_parse_failed(
    entries: list[tuple[str, bytes]],
    code: str,
    client: TestClient,
    queue: Mock,
    engine: Engine,
    settings: Settings,
) -> None:
    register(client)
    identifier = ready(client, entries)
    run_id = start(client, identifier)
    execute_analysis(run_id, engine, settings)
    result = client.get(f"/api/v1/projects/{identifier}/analyses/{run_id}").json()
    assert result["status"] == "FAILED"
    assert result["error_code"] == code


def test_mixed_languages_and_parse_warning(
    client: TestClient, queue: Mock, engine: Engine, settings: Settings
) -> None:
    settings.max_archive_files = 100
    register(client)
    entries = [
        (file.relative_to(FIXTURES).as_posix(), file.read_bytes())
        for file in sorted(FIXTURES.rglob("*"))
        if file.is_file()
    ]
    entries += [("bad.py", b"def ("), ("README.md", b"Unsupported inert data")]
    identifier = ready(client, entries)
    run_id = start(client, identifier)
    execute_analysis(run_id, engine, settings)
    result = client.get(f"/api/v1/projects/{identifier}/analyses/{run_id}").json()
    assert result["status"] == "COMPLETED", result
    assert result["summary"]["languages"] == [
        "java",
        "javascript",
        "python",
        "typescript",
    ]
    assert result["summary"]["unsupported_files"] == 1
    assert result["warnings"] == [
        {"code": "FILE_PARSE_FAILED", "relative_path": "bad.py"}
    ]


def test_worker_failure_redelivery_and_expiry(
    client: TestClient, queue: Mock, engine: Engine, settings: Settings
) -> None:
    register(client)
    identifier = ready(client)
    run_id = start(client, identifier)
    with Session(engine) as db:
        run = db.get(AnalysisRun, run_id)
        assert run
        run.status = RunStatus.RUNNING  # Simulated worker death before publication.
        db.commit()
    execute_analysis(run_id, engine, settings)
    with Session(engine) as db:
        assert db.get(AnalysisRun, run_id).status == RunStatus.COMPLETED  # type: ignore[union-attr]
    failed = start(client, identifier)
    with patch(
        "app.services.analysis.discover",
        side_effect=AnalysisFailure(
            "ANALYZER_TIMEOUT", "Analyzer time limit exceeded."
        ),
    ):
        execute_analysis(failed, engine, settings)
    assert (
        client.get(f"/api/v1/projects/{identifier}/analyses/{failed}").json()[
            "error_code"
        ]
        == "ANALYZER_TIMEOUT"
    )
    stale = start(client, identifier)
    with Session(engine) as db:
        run = db.get(AnalysisRun, stale)
        assert run
        run.deadline_at = now() - timedelta(seconds=1)
        db.commit()
    assert (
        client.get(f"/api/v1/projects/{identifier}/analyses/{stale}").json()[
            "error_code"
        ]
        == "ANALYSIS_EXPIRED"
    )
    execute_analysis(stale, engine, settings)
    assert (
        client.get(f"/api/v1/projects/{identifier}/analyses/{stale}").json()["status"]
        == "FAILED"
    )


def test_duplicate_worker_lock(
    client: TestClient, queue: Mock, engine: Engine, settings: Settings
) -> None:
    register(client)
    identifier = ready(client)
    run_id = start(client, identifier)
    with engine.connect() as connection:
        key = int.from_bytes(run_id.bytes[:8], "big", signed=True)
        connection.execute(text("SELECT pg_advisory_lock(:key)"), {"key": key})
        try:
            execute_analysis(run_id, engine, settings)
            assert (
                client.get(f"/api/v1/projects/{identifier}/analyses/{run_id}").json()[
                    "status"
                ]
                == "QUEUED"
            )
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
    execute_analysis(run_id, engine, settings)
    assert (
        client.get(f"/api/v1/projects/{identifier}/analyses/{run_id}").json()["status"]
        == "COMPLETED"
    )


def test_phase2_data_survives_upgrade_and_analysis_rollback(
    client: TestClient, queue: Mock, engine: Engine, settings: Settings
) -> None:
    register(client)
    identifier = ready(client)
    config = Config("alembic.ini")
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "6e605e1f5bed")
        command.upgrade(config, "head")
        command.check(config)
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.get(f"/api/v1/projects/{identifier}").json()["status"] == "READY"
    run_id = start(client, identifier)
    execute_analysis(run_id, engine, settings)
    assert (
        client.get(f"/api/v1/projects/{identifier}/analyses/{run_id}").json()["status"]
        == "COMPLETED"
    )
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "6e605e1f5bed")
        command.upgrade(config, "head")
    assert client.get(f"/api/v1/projects/{identifier}/analyses").json() == []
    assert client.get("/api/v1/auth/me").status_code == 200


def test_partial_tool_failure_publishes_no_entities_and_cleans_workspace(
    client: TestClient,
    queue: Mock,
    engine: Engine,
    settings: Settings,
    tmp_path: Path,
) -> None:
    from functools import partial
    from tempfile import TemporaryDirectory

    from app.analyzers.adapters import registry

    register(client)
    identifier = ready(
        client,
        [
            ("main.js", b"function run() { return 1; }"),
            ("main.py", b"def run(): return 1"),
        ],
    )
    run_id = start(client, identifier)
    adapters = registry()
    adapters["python"] = Mock(
        analyze=Mock(side_effect=RuntimeError("private source /secret/path"))
    )
    with (
        patch("app.services.analysis.registry", return_value=adapters),
        patch(
            "app.services.analysis.TemporaryDirectory",
            partial(TemporaryDirectory, dir=tmp_path),
        ),
    ):
        execute_analysis(run_id, engine, settings)
    result = client.get(f"/api/v1/projects/{identifier}/analyses/{run_id}")
    assert result.json()["status"] == "FAILED"
    assert "private source" not in result.text and "/secret/path" not in result.text
    assert (
        client.get(f"/api/v1/projects/{identifier}/analyses/{run_id}/entities").json()[
            "total"
        ]
        == 0
    )
    assert not list(tmp_path.glob("kagex-analysis-*"))
