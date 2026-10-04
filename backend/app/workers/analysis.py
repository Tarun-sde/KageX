from uuid import UUID

from app.core.config import Settings
from app.db.session import create_db_engine
from app.services.analysis import execute_analysis
from app.workers.celery_app import celery_app


@celery_app.task(
    name="kagex.analyze", acks_late=True, reject_on_worker_lost=True, ignore_result=True
)
def analyze_project(run_id: str) -> None:
    settings = Settings()
    engine = create_db_engine(settings)
    try:
        execute_analysis(UUID(run_id), engine, settings)
    finally:
        engine.dispose()
