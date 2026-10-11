"""Authentication business logic."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.jwt import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.config import settings
from app.exceptions import ConflictError, InvalidInputError, UnauthorizedError
from app.models import RefreshToken, User

logger = logging.getLogger(__name__)

# Valid bcrypt hash used to equalise timing when the email is unknown.
_DUMMY_HASH = hash_password("timing-equaliser-not-a-real-password")


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def register_user(db: Session, email: str, password: str, full_name: str) -> User:
    email = email.strip().lower()
    if get_user_by_email(db, email) is not None:
        raise ConflictError("Email already registered")
    try:
        hashed = hash_password(password)
    except ValueError as exc:
        raise InvalidInputError("Password must be at most 72 bytes") from exc
    user = User(
        email=email,
        hashed_password=hashed,
        full_name=full_name,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Email already registered") from exc
    db.refresh(user)
    logger.info("User registered id=%s", user.id)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    """Return the user or raise a generic 401 (never reveals if the email exists)."""
    user = get_user_by_email(db, email)
    hashed = user.hashed_password if user and user.hashed_password else _DUMMY_HASH
    password_ok = verify_password(password, hashed)
    if user is None or not user.hashed_password or not password_ok or not user.is_active:
        raise UnauthorizedError("Invalid email or password")
    return user


def issue_token_pair(db: Session, user: User) -> tuple[str, str]:
    """Create an access token and a persisted (hashed) refresh token."""
    raw, token_hash = generate_refresh_token()
    # Opportunistic housekeeping. Only expired tokens are removed; revoked-but-unexpired
    # ones are kept so rotated-token reuse (theft) detection keeps working.
    db.execute(
        delete(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.expires_at < datetime.now(UTC))
        .execution_options(synchronize_session=False)
    )
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            revoked=False,
        )
    )
    db.commit()
    return create_access_token(user.id), raw


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _find_refresh(db: Session, raw_token: str, *, lock: bool = False) -> RefreshToken | None:
    stmt = select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
    if lock:
        stmt = stmt.with_for_update()
    return db.scalar(stmt)


def revoke_all_refresh_tokens(db: Session, user_id: int) -> None:
    """Revoke every active refresh token of a user (caller commits)."""
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )


def refresh_tokens(db: Session, raw_token: str) -> tuple[str, str]:
    """Rotate: revoke the presented refresh token and issue a new pair."""
    record = _find_refresh(db, raw_token, lock=True)
    if record is None:
        raise UnauthorizedError("Invalid or expired refresh token")
    if record.revoked:
        # Reuse of a rotated/revoked token: assume theft, kill the whole family.
        logger.warning("Refresh token reuse detected user_id=%s", record.user_id)
        revoke_all_refresh_tokens(db, record.user_id)
        db.commit()
        raise UnauthorizedError("Invalid or expired refresh token")
    if _aware(record.expires_at) <= datetime.now(UTC):
        raise UnauthorizedError("Invalid or expired refresh token")
    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Invalid or expired refresh token")
    record.revoked = True
    db.flush()
    return issue_token_pair(db, user)


def logout(db: Session, raw_token: str) -> None:
    """Revoke a refresh token. Idempotent: unknown tokens are ignored."""
    record = _find_refresh(db, raw_token)
    if record is not None and not record.revoked:
        record.revoked = True
        db.commit()


def update_full_name(db: Session, user: User, full_name: str) -> User:
    user.full_name = full_name
    db.commit()
    db.refresh(user)
    return user
