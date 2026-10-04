from celery import Celery

from app.core.config import Settings


def create_celery(settings: Settings) -> Celery:
    app = Celery(
        "kagex",
        broker=settings.celery_broker_url.get_secret_value()
        or settings.redis_url.get_secret_value(),
        backend=settings.celery_result_backend.get_secret_value()
        or settings.redis_url.get_secret_value(),
        include=["app.workers.analysis"],
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        broker_connection_retry_on_startup=True,
        result_expires=3600,
        worker_prefetch_multiplier=1,
        task_soft_time_limit=settings.analysis_timeout_seconds + 10,
        task_time_limit=settings.analysis_timeout_seconds + 20,
        broker_connection_timeout=3,
        task_publish_retry=False,
        broker_transport_options={
            "socket_connect_timeout": 3,
            "socket_timeout": 3,
            "visibility_timeout": 900,
        },
    )
    return app
