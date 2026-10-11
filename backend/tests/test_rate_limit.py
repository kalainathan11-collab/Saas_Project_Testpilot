"""Rate limiting on unauthenticated auth endpoints."""

from fastapi.testclient import TestClient

from app.config import settings
from app.rate_limit import limiter


def _login(client: TestClient, email: str = "nobody@example.com") -> int:
    return client.post(
        "/auth/login", json={"email": email, "password": "wrong-password-1"}
    ).status_code


def test_login_per_email_limit_returns_429_with_retry_after(client: TestClient) -> None:
    limit = settings.RATE_LIMIT_LOGIN_PER_EMAIL
    for _ in range(limit):
        assert _login(client) == 401
    res = client.post("/auth/login", json={"email": "nobody@example.com", "password": "x" * 12})
    assert res.status_code == 429
    assert res.json()["error"]["code"] == "RATE_LIMITED"
    assert int(res.headers["Retry-After"]) >= 1


def test_login_limit_is_per_email_not_global(client: TestClient) -> None:
    for _ in range(settings.RATE_LIMIT_LOGIN_PER_EMAIL):
        _login(client, "a@example.com")
    assert _login(client, "b@example.com") == 401


def test_register_limit(client: TestClient) -> None:
    codes = [
        client.post(
            "/auth/register",
            json={"email": f"u{i}@example.com", "password": "Passw0rd!xyz", "full_name": "U"},
        ).status_code
        for i in range(settings.RATE_LIMIT_REGISTER_PER_IP + 1)
    ]
    assert codes[:-1] == [201] * settings.RATE_LIMIT_REGISTER_PER_IP
    assert codes[-1] == 429


def test_refresh_limit(client: TestClient) -> None:
    codes = [
        client.post("/auth/refresh", headers={"X-Requested-With": "TestPilot"}).status_code
        for _ in range(settings.RATE_LIMIT_REFRESH_PER_IP + 1)
    ]
    assert codes[-1] == 429
    assert set(codes[:-1]) == {401}


def test_limiter_window_expires() -> None:
    limiter.reset()
    for i in range(3):
        limiter.hit("k", 3, 60, now=1000.0 + i)
    try:
        limiter.hit("k", 3, 60, now=1010.0)
    except Exception as exc:  # RateLimitError
        assert getattr(exc, "status_code", 429) == 429
    else:
        raise AssertionError("expected rate limit")
    limiter.hit("k", 3, 60, now=1100.0)  # window passed: allowed again


def test_x_forwarded_for_ignored_unless_trusted(client: TestClient) -> None:
    assert settings.TRUSTED_PROXY is False
    for i in range(settings.RATE_LIMIT_LOGIN_PER_IP):
        res = client.post(
            "/auth/login",
            json={"email": f"e{i}@example.com", "password": "x" * 12},
            headers={"X-Forwarded-For": f"10.0.0.{i}"},
        )
        assert res.status_code == 401
    res = client.post(
        "/auth/login",
        json={"email": "z@example.com", "password": "x" * 12},
        headers={"X-Forwarded-For": "10.9.9.9"},
    )
    assert res.status_code == 429
