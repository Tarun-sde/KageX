from app.core.config import Settings
from app.workers.config import create_celery

settings = Settings()
celery_app = create_celery(settings)


@celery_app.task(name="kagex.ping")
def ping() -> str:
    """Verify queue transport without touching user source."""
    return "pong"
