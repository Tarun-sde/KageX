"""Persistent identity, sessions, and owned projects."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def now() -> datetime:
    return datetime.now(UTC)


class SourceType(StrEnum):
    ZIP_UPLOAD = "ZIP_UPLOAD"
    GITHUB = "GITHUB"


class ProjectStatus(StrEnum):
    CREATED = "CREATED"
    READY = "READY"
    FAILED = "FAILED"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("email = lower(email)", name="email_normalized"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now, server_default=func.now()
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint(
            "length(trim(name)) BETWEEN 1 AND 100", name="project_name_length"
        ),
        CheckConstraint(
            "file_count >= 0 AND source_bytes >= 0", name="source_sizes_nonnegative"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[SourceType] = mapped_column(
        SQLEnum(
            SourceType, name="source_type", native_enum=False, create_constraint=True
        )
    )
    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(
            ProjectStatus,
            name="project_status",
            native_enum=False,
            create_constraint=True,
        ),
        default=ProjectStatus.CREATED,
    )
    github_url: Mapped[str | None] = mapped_column(String(250))
    error_code: Mapped[str | None] = mapped_column(String(50))
    file_count: Mapped[int] = mapped_column(default=0, server_default="0")
    source_bytes: Mapped[int] = mapped_column(default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now, server_default=func.now()
    )
