from hashlib import sha256
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import APIError
from app.db.session import get_session
from app.models import AuthSession, User, now

DB = Annotated[Session, Depends(get_session)]


def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


Config = Annotated[Settings, Depends(get_settings)]


def cookie_name(settings: Settings) -> str:
    return (
        "__Host-kagex_session" if settings.app_env == "production" else "kagex_session"
    )


def token_hash(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def require_csrf(request: Request, settings: Config) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    if (
        request.headers.get("origin") not in settings.cors_allowed_origins
        or request.headers.get("x-kagex-request") != "1"
    ):
        raise APIError(403, "CSRF_REJECTED", "Request origin could not be verified.")


def get_current_user(request: Request, db: DB, settings: Config) -> User:
    token = request.cookies.get(cookie_name(settings), "")
    if not token or len(token) > 128:
        raise APIError(401, "UNAUTHENTICATED", "Sign in to continue.")
    user = db.scalar(
        select(User)
        .join(AuthSession, AuthSession.user_id == User.id)
        .where(
            AuthSession.token_hash == token_hash(token),
            AuthSession.expires_at > now(),
            User.is_active.is_(True),
        )
    )
    if user is None:
        raise APIError(401, "UNAUTHENTICATED", "Sign in to continue.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
