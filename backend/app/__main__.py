import uvicorn

from app.core.config import Settings

settings = Settings()
uvicorn.run(
    "app.main:create_app",
    factory=True,
    host=settings.backend_host,
    port=settings.backend_port,
    reload=settings.app_env == "development",
    log_level=settings.log_level.lower(),
)
