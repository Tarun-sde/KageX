import logging
import time
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from sqlalchemy import Engine, delete, select, text, update
from sqlalchemy.orm import Session

from app.analyzers.adapters import registry
from app.analyzers.contracts import AnalysisFailure, Entity
from app.analyzers.discovery import check_time, discover
from app.core.config import Settings
from app.models import now
from app.models.analysis import AnalysisEntity, AnalysisRun, RunStatus

logger = logging.getLogger(__name__)
ACTIVE = (RunStatus.QUEUED, RunStatus.RUNNING)


def expire_runs(db: Session, project_id: UUID) -> None:
    db.execute(
        update(AnalysisRun)
        .where(
            AnalysisRun.project_id == project_id,
            AnalysisRun.status.in_(ACTIVE),
            AnalysisRun.deadline_at <= now(),
        )
        .values(
            status=RunStatus.FAILED,
            completed_at=now(),
            error_code="ANALYSIS_EXPIRED",
            error_message="The analysis deadline expired. Start a new run.",
        )
    )


def execute_analysis(identifier: UUID, engine: Engine, settings: Settings) -> None:
    # Session advisory lock survives commits, releases on connection/process death.
    # Redeliveries cannot run the same job concurrently; terminal runs are no-ops.
    key = int.from_bytes(identifier.bytes[:8], "big", signed=True)
    with engine.connect() as connection:
        locked = connection.scalar(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
        )
        connection.commit()
        if not locked:
            return
        try:
            with Session(bind=connection) as db:
                run = db.scalar(
                    select(AnalysisRun)
                    .where(AnalysisRun.id == identifier)
                    .with_for_update()
                )
                if run is None or run.status not in ACTIVE:
                    return
                if run.deadline_at <= now():
                    expire_runs(db, run.project_id)
                    db.commit()
                    return
                project_id = run.project_id
                run.status = RunStatus.RUNNING
                run.started_at = now()
                # Redelivery never extends the original deadline.
                run.deadline_at = min(
                    run.deadline_at,
                    now() + timedelta(seconds=settings.analysis_timeout_seconds + 5),
                )
                deadline = time.monotonic() + min(
                    settings.analysis_timeout_seconds,
                    (run.deadline_at - now()).total_seconds(),
                )
                db.commit()
                logger.info("Analysis started run=%s", identifier)
                warnings: list[dict[str, str]] = []
                try:
                    entities: list[Entity] = []
                    with TemporaryDirectory(prefix="kagex-analysis-") as temporary:
                        workspace = Path(temporary)
                        source = settings.project_storage_root / str(project_id)
                        grouped, unsupported, warnings = discover(
                            source, workspace / "source", settings, deadline
                        )
                        if not grouped:
                            run.warnings = warnings
                            raise AnalysisFailure(
                                "NO_SUPPORTED_SOURCE",
                                "No supported source files could be analyzed.",
                            )
                        adapters = registry()
                        for language, paths in sorted(grouped.items()):
                            check_time(deadline)
                            logger.info(
                                "Analyzer started run=%s language=%s",
                                identifier,
                                language,
                            )
                            result = adapters[language].analyze(
                                workspace / "source", paths, settings, deadline
                            )
                            for entity in result.entities:
                                if (
                                    entity.relative_path not in paths
                                    or entity.language != language
                                    or entity.end_line < entity.start_line
                                ):
                                    raise AnalysisFailure(
                                        "ANALYZER_FAILED",
                                        "An analyzer returned invalid metadata.",
                                    )
                            entities.extend(result.entities)
                            if any(
                                w.get("relative_path") not in paths
                                for w in result.warnings
                            ):
                                raise AnalysisFailure(
                                    "ANALYZER_FAILED",
                                    "An analyzer returned invalid warning metadata.",
                                )
                            warnings.extend(result.warnings)
                            if len(entities) > settings.max_analysis_entities:
                                raise AnalysisFailure(
                                    "SOURCE_LIMIT_EXCEEDED",
                                    "The analysis contains too many entities.",
                                )
                    check_time(deadline)
                    # Lock only the final transaction; expiry/deletion may have won.
                    db.expire_all()
                    run = db.scalar(
                        select(AnalysisRun)
                        .where(AnalysisRun.id == identifier)
                        .with_for_update()
                    )
                    if run is None or run.status not in ACTIVE:
                        return
                    if run.deadline_at <= now():
                        raise AnalysisFailure(
                            "ANALYSIS_EXPIRED",
                            "The analysis deadline expired. Start a new run.",
                        )
                    if not entities:
                        run.warnings = warnings
                        raise AnalysisFailure(
                            "NO_ANALYZABLE_ENTITIES",
                            "No analyzable entities were found. Inspect the warnings.",
                        )
                    db.execute(
                        delete(AnalysisEntity).where(
                            AnalysisEntity.analysis_run_id == identifier
                        )
                    )
                    for entity in entities:
                        db.add(
                            AnalysisEntity(
                                analysis_run_id=identifier, **entity.model_dump()
                            )
                        )
                    run.summary = {
                        "supported_files": sum(map(len, grouped.values())),
                        "unsupported_files": unsupported,
                        "languages": sorted(grouped),
                        "entities_analyzed": len(entities),
                        "warning_count": len(warnings)
                        + sum(len(e.warnings) for e in entities),
                        "duration_seconds": round(
                            (now() - run.started_at).total_seconds(), 3
                        )
                        if run.started_at
                        else 0,
                        "analyzers": sorted(
                            {
                                f"{e.analyzer_name}:{e.analyzer_version}:{e.metric_schema_version}"
                                for e in entities
                            }
                        ),
                    }
                    run.warnings = warnings
                    run.status, run.completed_at = RunStatus.COMPLETED, now()
                    db.commit()
                    logger.info(
                        "Analysis completed run=%s entities=%s",
                        identifier,
                        len(entities),
                    )
                except Exception as error:
                    saved_warnings = warnings
                    db.rollback()
                    failure = (
                        error
                        if isinstance(error, AnalysisFailure)
                        else AnalysisFailure(
                            "ANALYSIS_FAILED",
                            "Static analysis failed. Start a new run to retry.",
                        )
                    )
                    db.execute(
                        update(AnalysisRun)
                        .where(
                            AnalysisRun.id == identifier, AnalysisRun.status.in_(ACTIVE)
                        )
                        .values(
                            status=RunStatus.FAILED,
                            completed_at=now(),
                            error_code=failure.code,
                            error_message=failure.message,
                            warnings=saved_warnings,
                        )
                    )
                    db.commit()
                    logger.warning(
                        "Analysis failed run=%s code=%s type=%s",
                        identifier,
                        failure.code,
                        type(error).__name__,
                    )
        finally:
            connection.rollback()
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
            connection.commit()
