"""Small in-process sliding-window rate limiter for unauthenticated auth endpoints.

NOTE: state lives in process memory. With several workers/instances each keeps its
own counters, so the effective limit is multiplied by the instance count. Multi-
instance deployments should back this with a shared store (e.g. Redis) or enforce
limits at the gateway/proxy.
"""

import threading
import time
from collections import deque

from fastapi import Request

from app.config import settings
from app.exceptions import RateLimitError

_MAX_KEYS = 50_000


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def hit(self, key: str, limit: int, window: float, now: float | None = None) -> None:
        """Record a hit; raise RateLimitError when `limit` hits already fall in `window`."""
        now = time.monotonic() if now is None else now
        with self._lock:
            if len(self._hits) > _MAX_KEYS:
                self._prune(now, window)
            q = self._hits.setdefault(key, deque())
            while q and q[0] <= now - window:
                q.popleft()
            if len(q) >= limit:
                raise RateLimitError(retry_after=int(q[0] + window - now) + 1)
            q.append(now)

    def _prune(self, now: float, window: float) -> None:
        for k in [k for k, q in self._hits.items() if not q or q[-1] <= now - window]:
            del self._hits[k]


limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    """Client IP; X-Forwarded-For is honoured only when TRUSTED_PROXY is enabled.

    The right-most entry is the one appended by our own proxy; earlier entries
    are client-controlled and therefore spoofable.
    """
    if settings.TRUSTED_PROXY:
        forwarded = request.headers.get("x-forwarded-for", "")
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            return parts[-1]
    return request.client.host if request.client else "unknown"


def limit_login(request: Request, email: str) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return
    ip = client_ip(request)
    limiter.hit(f"login:ip:{ip}", settings.RATE_LIMIT_LOGIN_PER_IP, 60)
    limiter.hit(
        f"login:ip-email:{ip}:{email.strip().lower()}", settings.RATE_LIMIT_LOGIN_PER_EMAIL, 60
    )


def limit_register(request: Request) -> None:
    if settings.RATE_LIMIT_ENABLED:
        limiter.hit(f"register:ip:{client_ip(request)}", settings.RATE_LIMIT_REGISTER_PER_IP, 3600)


def limit_refresh(request: Request) -> None:
    if settings.RATE_LIMIT_ENABLED:
        limiter.hit(f"refresh:ip:{client_ip(request)}", settings.RATE_LIMIT_REFRESH_PER_IP, 60)
