"""Public contracts. Persistence models are never serialized directly."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    StringConstraints,
    field_validator,
)

from app.models import ProjectStatus, SourceType


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    email: EmailStr = Field(max_length=254)
    password: SecretStr = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str


ProjectName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: ProjectName
    source_type: SourceType


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: ProjectName


class GitHubInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(min_length=1, max_length=250)


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    source_type: SourceType
    status: ProjectStatus
    github_url: str | None
    error_code: str | None
    file_count: int
    source_bytes: int
    created_at: datetime
    updated_at: datetime
