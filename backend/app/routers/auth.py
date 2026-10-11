"""Auth endpoints: /auth/*."""

import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, Query, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse

from app import rate_limit
from app.auth import oauth
from app.config import settings
from app.dependencies import CurrentUser, DbSession
from app.exceptions import AppError, ForbiddenError, UnauthorizedError
from app.schemas.auth import (
    AccessToken,
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UserOut,
)
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


REFRESH_COOKIE = "tp_refresh"
REFRESH_COOKIE_PATH = "/auth"
CSRF_HEADER = "x-requested-with"
CSRF_HEADER_VALUE = "TestPilot"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path=REFRESH_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.COOKIE_SAMESITE,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        REFRESH_COOKIE,
        path=REFRESH_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.COOKIE_SAMESITE,
    )


def _require_csrf(request: Request) -> None:
    """CSRF defence for cookie-authenticated endpoints: Origin allowlist + custom header."""
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins_list:
        raise ForbiddenError("Origin not allowed")
    if request.headers.get(CSRF_HEADER) != CSRF_HEADER_VALUE:
        raise ForbiddenError("Missing or invalid X-Requested-With header")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, request: Request, db: DbSession) -> UserOut:
    rate_limit.limit_register(request)
    user = auth_service.register_user(db, body.email, body.password, body.full_name)
    return UserOut.model_validate(user)


@router.post("/login", response_model=AccessToken)
def login(body: LoginRequest, request: Request, response: Response, db: DbSession) -> AccessToken:
    rate_limit.limit_login(request, body.email)
    user = auth_service.authenticate(db, body.email, body.password)
    access, refresh_token = auth_service.issue_token_pair(db, user)
    _set_refresh_cookie(response, refresh_token)
    return AccessToken(access_token=access)


@router.post("/refresh", response_model=AccessToken)
def refresh(request: Request, db: DbSession) -> Response:
    _require_csrf(request)
    rate_limit.limit_refresh(request)
    raw = request.cookies.get(REFRESH_COOKIE)
    try:
        if not raw:
            raise UnauthorizedError("Invalid or expired refresh token")
        access, new_refresh = auth_service.refresh_tokens(db, raw)
    except UnauthorizedError as exc:
        error = JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
        )
        _clear_refresh_cookie(error)
        return error
    response = JSONResponse(
        content=AccessToken(access_token=access).model_dump(),
        headers={"Cache-Control": "no-store"},
    )
    _set_refresh_cookie(response, new_refresh)
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: DbSession) -> Response:
    _require_csrf(request)
    raw = request.cookies.get(REFRESH_COOKIE)
    if raw:
        auth_service.logout(db, raw)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_refresh_cookie(response)
    return response


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.put("/me", response_model=UserOut)
def update_me(body: UpdateProfileRequest, user: CurrentUser, db: DbSession) -> UserOut:
    updated = auth_service.update_full_name(db, user, body.full_name)
    return UserOut.model_validate(updated)


STATE_COOKIE = "oauth_state_nonce"
STATE_COOKIE_PATH = "/auth"
STATE_COOKIE_MAX_AGE = 600


def _cookie_secure() -> bool:
    return settings.cookie_secure


def _clear_state_cookie(response: Response) -> None:
    response.delete_cookie(
        STATE_COOKIE,
        path=STATE_COOKIE_PATH,
        secure=_cookie_secure(),
        httponly=True,
        samesite="lax",
    )


@router.get("/google")
def google_login() -> RedirectResponse:
    url, nonce = oauth.build_authorization_url()
    response = RedirectResponse(url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        STATE_COOKIE,
        nonce,
        max_age=STATE_COOKIE_MAX_AGE,
        path=STATE_COOKIE_PATH,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
    )
    return response


@router.get("/google/callback")
def google_callback(
    db: DbSession,
    code: Annotated[str, Query(min_length=1)],
    state: Annotated[str, Query(min_length=1)],
    oauth_state_nonce: Annotated[str | None, Cookie()] = None,
) -> Response:
    try:
        user = oauth.authenticate_with_google(db, code, state, oauth_state_nonce)
        _access, refresh_token = auth_service.issue_token_pair(db, user)
    except AppError as exc:
        headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, UnauthorizedError) else None
        error = JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers=headers,
        )
        error.headers["Cache-Control"] = "no-store"
        _clear_state_cookie(error)
        return error
    # No tokens in the URL: the refresh token goes in an HttpOnly cookie and the
    # frontend obtains its access token via POST /auth/refresh.
    response = RedirectResponse(
        f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback",
        status_code=status.HTTP_302_FOUND,
    )
    _set_refresh_cookie(response, refresh_token)
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    _clear_state_cookie(response)
    return response
