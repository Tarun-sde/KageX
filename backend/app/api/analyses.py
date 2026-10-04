import logging
from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.api.projects import OwnedProject
from app.core.errors import APIError
from app.core.security import DB, Config, require_csrf
from app.models import ProjectStatus, now
from app.models.analysis import AnalysisEntity, AnalysisRun, RunStatus
from app.schemas.analysis import EntityOut, EntityPage, RunOut
from app.services.analysis import ACTIVE, expire_runs

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/analyses",
    tags=["Static analysis"],
    dependencies=[Depends(require_csrf)],
)
logger = logging.getLogger(__name__)


@router.post("", status_code=202, response_model=RunOut)
def start_analysis(
    project: OwnedProject, db: DB, settings: Config, request: Request
) -> AnalysisRun:
    if project.status != ProjectStatus.READY:
        raise APIError(
            409, "PROJECT_NOT_READY", "Prepare project source before starting analysis."
        )
    expire_runs(db, project.id)
    if (
        db.scalar(
            select(AnalysisRun.id).where(
                AnalysisRun.project_id == project.id, AnalysisRun.status.in_(ACTIVE)
            )
        )
        is not None
    ):
        raise APIError(
            409,
            "ANALYSIS_ALREADY_RUNNING",
            "This project already has an active analysis.",
        )
    run = AnalysisRun(
        project_id=project.id,
        deadline_at=now() + timedelta(seconds=settings.analysis_queue_timeout_seconds),
    )
    db.add(run)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise APIError(
            409,
            "ANALYSIS_ALREADY_RUNNING",
            "This project already has an active analysis.",
        ) from error
    identifier = run.id
    try:
        request.app.state.celery.send_task(
            "kagex.analyze",
            args=[str(identifier)],
            task_id=str(identifier),
            expires=settings.analysis_queue_timeout_seconds,
        )
    except Exception as error:
        # Even an ambiguous broker acknowledgement cannot overwrite worker success.
        db.execute(
            update(AnalysisRun)
            .where(AnalysisRun.id == identifier, AnalysisRun.status == RunStatus.QUEUED)
            .values(
                status=RunStatus.FAILED,
                completed_at=now(),
                error_code="QUEUE_UNAVAILABLE",
                error_message="The analysis queue is unavailable. Start a new run.",
            )
        )
        db.commit()
        logger.warning(
            "Analysis enqueue failed run=%s type=%s", identifier, type(error).__name__
        )
        raise APIError(
            503, "QUEUE_UNAVAILABLE", "The analysis queue is unavailable. Please retry."
        ) from error
    logger.info("Analysis queued run=%s", identifier)
    db.refresh(run)
    return run


@router.get("", response_model=list[RunOut])
def list_runs(
    project: OwnedProject, db: DB, offset: Annotated[int, Query(ge=0)] = 0
) -> list[AnalysisRun]:
    expire_runs(db, project.id)
    db.commit()
    return list(
        db.scalars(
            select(AnalysisRun)
            .where(AnalysisRun.project_id == project.id)
            .order_by(AnalysisRun.created_at.desc(), AnalysisRun.id)
            .offset(offset)
            .limit(50)
        )
    )


def owned_run(run_id: UUID, project: OwnedProject, db: DB) -> AnalysisRun:
    expire_runs(db, project.id)
    db.commit()
    run = db.scalar(
        select(AnalysisRun).where(
            AnalysisRun.id == run_id, AnalysisRun.project_id == project.id
        )
    )
    if run is None:
        raise APIError(404, "ANALYSIS_NOT_FOUND", "Analysis not found.")
    return run


OwnedRun = Annotated[AnalysisRun, Depends(owned_run)]


@router.get("/{run_id}", response_model=RunOut)
def get_run(run: OwnedRun) -> AnalysisRun:
    return run


@router.get("/{run_id}/entities", response_model=EntityPage)
def get_entities(
    run: OwnedRun,
    db: DB,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    language: Annotated[
        str | None, Query(pattern="^(java|python|javascript|typescript)$")
    ] = None,
) -> EntityPage:
    query = select(AnalysisEntity).where(AnalysisEntity.analysis_run_id == run.id)
    if language:
        query = query.where(AnalysisEntity.language == language)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(
            AnalysisEntity.relative_path, AnalysisEntity.start_line, AnalysisEntity.id
        )
        .offset(offset)
        .limit(limit)
    )
    return EntityPage(
        items=[EntityOut.model_validate(row) for row in rows],
        total=total,
        offset=offset,
        limit=limit,
    )
