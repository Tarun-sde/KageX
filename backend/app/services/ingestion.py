import logging
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import APIError
from app.models import Project, ProjectStatus
from app.services.storage import Storage, extract_archive

logger = logging.getLogger(__name__)


@contextmanager
def preparation_workspace(
    project: Project, db: Session, settings: Settings
) -> Iterator[tuple[Storage, Path]]:
    with ExitStack() as cleanup:
        try:
            storage = Storage(settings)
            stage = cleanup.enter_context(storage.staging())
        except (OSError, APIError) as error:
            project.status = ProjectStatus.FAILED
            project.error_code = "STORAGE_UNAVAILABLE"
            db.commit()
            raise APIError(
                503, "STORAGE_UNAVAILABLE", "Source storage is unavailable."
            ) from error
        yield storage, stage


def ingest(
    project: Project,
    db: Session,
    storage: Storage,
    stage: Path,
    archive: Path,
    deadline: float,
    fetch: Callable[[], None] | None = None,
) -> Project:
    """Caller holds the project's row lock, including throughout upload/download."""
    project_id = project.id
    published = False
    logger.info("Ingestion started project=%s", project.id)
    try:
        if fetch:
            fetch()
        count, size = extract_archive(
            archive, stage / "source", storage.settings, deadline
        )
        storage.publish(stage / "source", project.id)
        published = True
        project.status = ProjectStatus.READY
        project.error_code = None
        project.file_count, project.source_bytes = count, size
        db.commit()
    except APIError as error:
        project.status, project.error_code = ProjectStatus.FAILED, error.code
        db.commit()
        logger.warning("Ingestion failed project=%s code=%s", project_id, error.code)
        raise
    except Exception as error:
        db.rollback()
        if published:
            storage.remove(project_id)
        failure = APIError(
            503, "INGESTION_FAILED", "Source preparation failed. Please retry."
        )
        # Re-lock after rollback; do not overwrite a later successful request.

        current = db.scalar(
            select(Project).where(Project.id == project_id).with_for_update()
        )
        if current is not None and current.status != ProjectStatus.READY:
            current.status, current.error_code = ProjectStatus.FAILED, failure.code
            db.commit()
        logger.warning("Ingestion failed project=%s code=%s", project_id, failure.code)
        raise failure from error
    logger.info("Ingestion succeeded project=%s", project.id)
    return project
