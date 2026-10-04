import logging
from typing import Literal, cast

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app import __version__

router = APIRouter()
logger = logging.getLogger(__name__)


class Health(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "kagex-api"
    version: str = __version__


class Readiness(BaseModel):
    status: Literal["ready", "unavailable"]
    postgres: bool
    redis: bool


@router.get("/health", response_model=Health)
def health() -> Health:
    return Health()


@router.get("/ready", response_model=Readiness)
def ready(request: Request, response: Response) -> Readiness:
    postgres_ok = redis_ok = False
    try:
        with cast(Engine, request.app.state.engine).connect() as connection:
            connection.execute(text("SELECT 1"))
        postgres_ok = True
    except SQLAlchemyError as error:
        logger.warning("PostgreSQL readiness failed: %s", type(error).__name__)
    try:
        redis_ok = bool(cast(Redis, request.app.state.redis).ping())
    except RedisError as error:
        logger.warning("Redis readiness failed: %s", type(error).__name__)
    is_ready = postgres_ok and redis_ok
    response.status_code = 200 if is_ready else 503
    return Readiness(
        status="ready" if is_ready else "unavailable",
        postgres=postgres_ok,
        redis=redis_ok,
    )
