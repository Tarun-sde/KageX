from collections.abc import Iterator
from typing import cast

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import Settings


class Base(DeclarativeBase):
    """Shared metadata for future models; no domain tables in Phase 1."""


def create_db_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_timeout=3,
        connect_args={"connect_timeout": 3, "options": "-c statement_timeout=3000"},
    )


def get_session(request: Request) -> Iterator[Session]:
    with Session(cast(Engine, request.app.state.engine)) as session:
        yield session
