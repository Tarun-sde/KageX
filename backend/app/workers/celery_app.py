from celery import Celery

from app.core.config import Settings

settings = Settings()
celery_app = Celery(
    "kagex",
    broker=settings.celery_broker_url.get_secret_value()
    or settings.redis_url.get_secret_value(),
    backend=settings.celery_result_backend.get_secret_value()
    or settings.redis_url.get_secret_value(),
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
)


@celery_app.task(name="kagex.ping")
def ping() -> str:
    """Verify queue transport without touching user source."""
    return "pong"
