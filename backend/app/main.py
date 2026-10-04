import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis

from app import __version__
from app.api import auth, health, projects, status
from app.core.body_limit import BodyLimitMiddleware
from app.core.config import Settings
from app.core.errors import register_error_handlers
from app.db.session import create_db_engine


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logging.basicConfig(
            level=settings.log_level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        logging.getLogger(__name__).info(
            "API starting environment=%s", settings.app_env
        )
        engine = create_db_engine(settings)
        redis = Redis.from_url(
            settings.redis_url.get_secret_value(),
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        app.state.engine = engine
        app.state.redis = redis
        try:
            yield
        finally:
            redis.close()
            engine.dispose()

    app = FastAPI(title="KageX API", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        BodyLimitMiddleware, upload_limit=settings.max_upload_size_mb * 1024 * 1024
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_credentials=True,
        allow_headers=["Content-Type", "X-KageX-Request"],
    )
    register_error_handlers(app)
    app.include_router(projects.router)
    app.include_router(auth.router)
    app.include_router(health.router)
    app.include_router(status.router)
    return app
