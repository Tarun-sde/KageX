from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.analyzers.contracts import Entity
from app.models.analysis import RunStatus


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    status: RunStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    summary: dict[str, object]
    warnings: list[dict[str, str]]


class EntityOut(Entity):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class EntityPage(BaseModel):
    items: list[EntityOut]
    total: int
    offset: int
    limit: int
