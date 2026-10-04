from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models import now


class RunStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        Index("ix_analysis_runs_project_created", "project_id", "created_at"),
        Index(
            "uq_analysis_active_project",
            "project_id",
            unique=True,
            postgresql_where=text("status IN ('QUEUED', 'RUNNING')"),
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    status: Mapped[RunStatus] = mapped_column(
        SQLEnum(
            RunStatus, name="run_status", native_enum=False, create_constraint=True
        ),
        default=RunStatus.QUEUED,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(String(200))
    summary: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    warnings: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)


class AnalysisEntity(Base):
    __tablename__ = "analysis_entities"
    __table_args__ = (
        UniqueConstraint(
            "analysis_run_id",
            "language",
            "relative_path",
            "qualified_name",
            "start_line",
            name="uq_analysis_entity_identity",
        ),
        Index(
            "ix_analysis_entities_run_language_id", "analysis_run_id", "language", "id"
        ),
        CheckConstraint(
            "start_line >= 1 AND end_line >= start_line", name="entity_line_range"
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE")
    )
    language: Mapped[str] = mapped_column(String(20))
    entity_type: Mapped[str] = mapped_column(String(20))
    relative_path: Mapped[str] = mapped_column(String(512))
    qualified_name: Mapped[str] = mapped_column(String(1024))
    start_line: Mapped[int] = mapped_column()
    end_line: Mapped[int] = mapped_column()
    metrics: Mapped[dict[str, int | float | None]] = mapped_column(JSONB)
    analyzer_name: Mapped[str] = mapped_column(String(100))
    analyzer_version: Mapped[str] = mapped_column(String(100))
    metric_schema_version: Mapped[str] = mapped_column(String(60))
    warnings: Mapped[list[str]] = mapped_column(JSONB, default=list)
