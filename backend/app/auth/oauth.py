"""Google OAuth authorization-code flow."""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import AppError, UnauthorizedError
from app.models import User
from app.services.auth_service import get_user_by_email, revoke_all_refresh_tokens

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
STATE_TTL_MINUTES = 10


class OAuthNotConfiguredError(AppError):
    status_code = 501
    code = "OAUTH_NOT_CONFIGURED"

    def __init__(self) -> None:
        super().__init__("Google OAuth is not configured")


class OAuthStateError(AppError):
    status_code = 400
    code = "OAUTH_STATE_MISMATCH"

    def __init__(self) -> None:
        super().__init__("OAuth state does not match this browser session")


class OAuthFailedError(AppError):
    status_code = 502
    code = "OAUTH_FAILED"

    def __init__(self, message: str = "Google sign-in failed") -> None:
        super().__init__(message)


def ensure_configured() -> None:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise OAuthNotConfiguredError()


def create_state() -> tuple[str, str]:
    """Signed, short-lived state JWT bound to a random nonce; returns (state, nonce).

    The nonce is also set in an HttpOnly cookie so the callback can prove the
    browser that finished the flow is the one that started it (login CSRF).
    """
    now = datetime.now(UTC)
    nonce = secrets.token_urlsafe(16)
    state = jwt.encode(
        {
            "type": "oauth_state",
            "nonce": nonce,
            "iat": now,
            "exp": now + timedelta(minutes=STATE_TTL_MINUTES),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return state, nonce


def verify_state(state: str, cookie_nonce: str | None) -> None:
    try:
        data = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid OAuth state") from exc
    if data.get("type") != "oauth_state":
        raise UnauthorizedError("Invalid OAuth state")
    expected = data.get("nonce")
    if (
        not cookie_nonce
        or not isinstance(expected, str)
        or not secrets.compare_digest(cookie_nonce.encode(), expected.encode())
    ):
        raise OAuthStateError()


def build_authorization_url() -> tuple[str, str]:
    """Return (google_url, nonce)."""
    ensure_configured()
    state, nonce = create_state()
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}", nonce


def fetch_google_profile(code: str) -> dict[str, Any]:
    """Exchange the authorization code and return the Google userinfo payload."""
    try:
        with httpx.Client(timeout=10.0) as client:
            token_resp = client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                logger.warning("Google token exchange failed: %s", token_resp.status_code)
                raise OAuthFailedError("Invalid Google authorization code")
            google_token = token_resp.json().get("access_token")
            if not google_token:
                raise OAuthFailedError()
            info_resp = client.get(
                GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {google_token}"}
            )
            if info_resp.status_code != 200:
                logger.warning("Google userinfo failed: %s", info_resp.status_code)
                raise OAuthFailedError()
            profile: dict[str, Any] = info_resp.json()
    except httpx.HTTPError as exc:
        logger.exception("Google OAuth network error")
        raise OAuthFailedError("Could not reach Google") from exc
    return profile


def get_or_create_user(db: Session, profile: dict[str, Any]) -> User:
    email = str(profile.get("email", "")).strip().lower()
    if not email or not profile.get("email_verified", False):
        raise OAuthFailedError("Google account email is not verified")
    user = get_user_by_email(db, email)
    if user is None:
        user = User(
            email=email,
            hashed_password=None,
            full_name=str(profile.get("name") or email.split("@")[0])[:100],
            is_active=True,
            is_verified=True,
            oauth_provider="google",
        )
        db.add(user)
    else:
        if not user.is_active:
            raise UnauthorizedError("Account is disabled")
        # Link. Pre-hijack defence: an attacker may have pre-registered this email
        # with a password they know. Drop that credential and all sessions.
        if user.hashed_password:
            user.hashed_password = None
            revoke_all_refresh_tokens(db, user.id)
        user.is_verified = True
        if not user.oauth_provider:
            user.oauth_provider = "google"
        if not user.full_name and profile.get("name"):
            user.full_name = str(profile["name"])[:100]
    db.commit()
    db.refresh(user)
    return user


def authenticate_with_google(db: Session, code: str, state: str, cookie_nonce: str | None) -> User:
    ensure_configured()
    verify_state(state, cookie_nonce)
    profile = fetch_google_profile(code)
    return get_or_create_user(db, profile)
