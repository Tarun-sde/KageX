import asyncio
import logging
import time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect

from app.core.errors import APIError
from app.core.security import DB, Config, CurrentUser, require_csrf
from app.models import Project, ProjectStatus, SourceType
from app.schemas import GitHubInput, ProjectCreate, ProjectOut, ProjectUpdate
from app.services.github import download_github, parse_github_url
from app.services.ingestion import ingest, preparation_workspace
from app.services.storage import MIB, Storage

router = APIRouter(
    prefix="/api/v1/projects", tags=["Projects"], dependencies=[Depends(require_csrf)]
)
logger = logging.getLogger(__name__)


def get_owned_project(
    project_id: UUID, user: CurrentUser, db: DB, request: Request
) -> Project:
    query = select(Project).where(Project.id == project_id, Project.owner_id == user.id)
    if request.method != "GET":
        query = query.with_for_update(nowait=True)
    try:
        project = db.scalar(query)
    except OperationalError as error:
        db.rollback()
        if getattr(error.orig, "sqlstate", None) != "55P03":
            raise
        raise APIError(
            409, "PROJECT_BUSY", "Another change is in progress. Try again shortly."
        ) from error
    if project is None:
        raise APIError(404, "PROJECT_NOT_FOUND", "Project not found.")
    return project


OwnedProject = Annotated[Project, Depends(get_owned_project)]


def allow_source(project: Project, expected: SourceType) -> None:
    if project.source_type != expected:
        raise APIError(
            400, "UNSUPPORTED_SOURCE", "This source does not match the project type."
        )
    if project.status == ProjectStatus.READY:
        raise APIError(
            409,
            "SOURCE_EXISTS",
            "Source is already prepared. Create a new project for another source.",
        )


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(data: ProjectCreate, user: CurrentUser, db: DB) -> Project:
    project = Project(owner_id=user.id, name=data.name, source_type=data.source_type)
    db.add(project)
    db.commit()
    logger.info("Project created project=%s", project.id)
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(
    user: CurrentUser,
    db: DB,
    response: Response,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Project]:
    response.headers["Cache-Control"] = "no-store"
    return list(
        db.scalars(
            select(Project)
            .where(Project.owner_id == user.id)
            .order_by(Project.created_at.desc(), Project.id)
            .offset(offset)
            .limit(50)
        )
    )


@router.get("/source-limits")
def source_limits(user: CurrentUser, settings: Config) -> dict[str, int]:
    return {"max_upload_bytes": settings.max_upload_size_mb * MIB}


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project: OwnedProject, response: Response) -> Project:
    response.headers["Cache-Control"] = "no-store"
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(data: ProjectUpdate, project: OwnedProject, db: DB) -> Project:
    project.name = data.name
    db.commit()
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project: OwnedProject, db: DB, settings: Config) -> None:
    try:
        with Storage(settings).deleting(project.id):
            db.delete(project)
            db.commit()
    except OSError as error:
        db.rollback()
        raise APIError(
            503, "STORAGE_UNAVAILABLE", "Source cleanup failed. Please retry."
        ) from error
    logger.info("Project deleted project=%s", project.id)


@router.post(
    "/{project_id}/source/zip",
    response_model=ProjectOut,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/zip": {"schema": {"type": "string", "format": "binary"}}
            },
        }
    },
)
async def upload_zip(
    request: Request, project: OwnedProject, db: DB, settings: Config
) -> Project:
    allow_source(project, SourceType.ZIP_UPLOAD)
    deadline = time.monotonic() + settings.ingestion_timeout_seconds
    # Raw ZIP body avoids unbounded multipart parsing/spooling before authorization.
    with preparation_workspace(project, db, settings) as (storage, stage):
        archive = stage / "upload.zip"
        try:
            size = 0
            async with asyncio.timeout(settings.ingestion_timeout_seconds):
                with archive.open("xb") as output:
                    async for chunk in request.stream():
                        size += len(chunk)
                        if size > settings.max_upload_size_mb * MIB:
                            raise APIError(
                                413,
                                "UPLOAD_TOO_LARGE",
                                "The archive exceeds the upload limit.",
                            )
                        output.write(chunk)
        except (APIError, TimeoutError, OSError, ClientDisconnect) as error:
            failure = (
                error
                if isinstance(error, APIError)
                else (
                    APIError(
                        408, "INGESTION_TIMEOUT", "The upload exceeded its time limit."
                    )
                    if isinstance(error, TimeoutError)
                    else APIError(
                        503, "INGESTION_FAILED", "The upload failed. Please retry."
                    )
                )
            )
            project.status, project.error_code = ProjectStatus.FAILED, failure.code
            db.commit()
            raise failure from error
        return await run_in_threadpool(
            ingest, project, db, storage, stage, archive, deadline
        )


@router.post("/{project_id}/source/github", response_model=ProjectOut)
def import_github(
    data: GitHubInput, project: OwnedProject, db: DB, settings: Config
) -> Project:
    allow_source(project, SourceType.GITHUB)
    owner, repo = parse_github_url(data.url)
    project.github_url = f"https://github.com/{owner}/{repo}"
    deadline = time.monotonic() + settings.ingestion_timeout_seconds
    with preparation_workspace(project, db, settings) as (storage, stage):
        archive = stage / "download.zip"
        return ingest(
            project,
            db,
            storage,
            stage,
            archive,
            deadline,
            lambda: download_github(owner, repo, archive, settings, deadline),
        )
