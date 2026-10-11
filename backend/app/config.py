"""Application settings loaded from environment variables / .env."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_MARKERS = (
    "change-me",
    "changeme",
    "your-secret",
    "secret-key",
    "replace-me",
    "placeholder",
    "not-for-production",
)


class Settings(BaseSettings):
    """Typed settings. Secrets must be supplied via environment, never hardcoded."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "TestPilot"
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:5173"
    # Comma-separated list of allowed origins.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Refresh-token cookie (tp_refresh).
    COOKIE_SAMESITE: Literal["strict", "lax", "none"] = "strict"
    # None -> derived: true when FRONTEND_URL is https.
    COOKIE_SECURE: bool | None = None
    COOKIE_DOMAIN: str | None = None

    # Rate limiting (in-process; see app/rate_limit.py for multi-instance caveats).
    RATE_LIMIT_ENABLED: bool = True
    # Honour X-Forwarded-For only when running behind a proxy you control.
    TRUSTED_PROXY: bool = False
    RATE_LIMIT_LOGIN_PER_IP: int = 10  # per minute
    RATE_LIMIT_LOGIN_PER_EMAIL: int = 5  # per minute, per (IP, email)
    RATE_LIMIT_REGISTER_PER_IP: int = 10  # per hour
    RATE_LIMIT_REFRESH_PER_IP: int = 30  # per minute

    @field_validator("CORS_ORIGINS")
    @classmethod
    def _no_wildcard_origin(cls, v: str) -> str:
        origins = [o.strip() for o in v.split(",") if o.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must list at least one origin")
        if any("*" in o for o in origins):
            raise ValueError("CORS_ORIGINS must not contain '*'; list explicit origins")
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def _strong_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        lowered = v.lower()
        if any(p in lowered for p in _PLACEHOLDER_MARKERS):
            raise ValueError("SECRET_KEY looks like a placeholder; generate a random value")
        return v

    @field_validator("COOKIE_SECURE", "COOKIE_DOMAIN", mode="before")
    @classmethod
    def _empty_is_none(cls, v: object) -> object:
        return None if isinstance(v, str) and not v.strip() else v

    @property
    def cookie_secure(self) -> bool:
        if self.COOKIE_SECURE is not None:
            return self.COOKIE_SECURE
        return self.FRONTEND_URL.lower().startswith("https")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
