import secrets
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.core.errors import APIError
from app.core.security import (
    DB,
    Config,
    CurrentUser,
    cookie_name,
    require_csrf,
    token_hash,
)
from app.models import AuthSession, User, now
from app.schemas import Credentials, UserOut

router = APIRouter(
    prefix="/api/v1/auth", tags=["Authentication"], dependencies=[Depends(require_csrf)]
)
password_hasher = PasswordHasher()
# Equal-cost password verification for nonexistent accounts; not a usable credential.
dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))


def issue_session(
    user: User, request: Request, response: Response, db: DB, settings: Config
) -> None:
    previous = request.cookies.get(cookie_name(settings), "")
    db.execute(
        delete(AuthSession).where(AuthSession.token_hash == token_hash(previous))
    )
    db.execute(
        delete(AuthSession).where(
            AuthSession.user_id == user.id, AuthSession.expires_at <= now()
        )
    )
    token = secrets.token_urlsafe(32)
    db.add(
        AuthSession(
            token_hash=token_hash(token),
            user_id=user.id,
            expires_at=now() + timedelta(seconds=settings.session_ttl_seconds),
        )
    )
    db.commit()
    response.set_cookie(
        cookie_name(settings),
        token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"


@router.post("/register", response_model=UserOut, status_code=201)
def register(
    data: Credentials, request: Request, response: Response, db: DB, settings: Config
) -> User:
    user = User(
        email=str(data.email),
        password_hash=password_hasher.hash(data.password.get_secret_value()),
    )
    db.add(user)
    try:
        db.flush()
        issue_session(user, request, response, db, settings)
    except IntegrityError as error:
        db.rollback()
        raise APIError(
            409, "EMAIL_REGISTERED", "This email is already registered."
        ) from error
    return user


@router.post("/login", response_model=UserOut)
def login(
    data: Credentials, request: Request, response: Response, db: DB, settings: Config
) -> User:
    user = db.scalar(select(User).where(User.email == str(data.email)))
    try:
        password_hasher.verify(
            user.password_hash if user else dummy_hash, data.password.get_secret_value()
        )
    except VerificationError as error:
        raise APIError(
            401, "INVALID_CREDENTIALS", "Invalid email or password."
        ) from error
    if user is None or not user.is_active:
        raise APIError(401, "INVALID_CREDENTIALS", "Invalid email or password.")
    if password_hasher.check_needs_rehash(user.password_hash):
        user.password_hash = password_hasher.hash(data.password.get_secret_value())
    issue_session(user, request, response, db, settings)
    return user


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser, response: Response) -> User:
    response.headers["Cache-Control"] = "no-store"
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: DB, settings: Config) -> None:
    token = request.cookies.get(cookie_name(settings), "")
    db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(token)))
    db.commit()
    response.delete_cookie(
        cookie_name(settings),
        path="/",
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
