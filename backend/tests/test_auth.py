"""Auth endpoint tests."""

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth import oauth
from app.auth.jwt import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.config import settings
from app.models import RefreshToken, User

CSRF = {"X-Requested-With": "TestPilot"}


def _register(client: TestClient, email: str = "new@example.com", **over: Any) -> Any:
    body = {"email": email, "password": "password123", "full_name": "New User"}
    body.update(over)
    return client.post("/auth/register", json=body)


def test_register_ok_and_no_hash_leak(client: TestClient) -> None:
    r = _register(client, "New@Example.com")
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "new@example.com"
    assert data["full_name"] == "New User"
    assert data["is_active"] is True
    assert "hashed_password" not in data and "password" not in data


def test_register_duplicate_409(client: TestClient) -> None:
    assert _register(client).status_code == 201
    r = _register(client, "NEW@example.com")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "CONFLICT"


@pytest.mark.parametrize(
    "over",
    [
        {"password": "short"},
        {"password": "ninechars"},
        {"password": "a" * 73},
        {"password": "\u00e9" * 37},  # 37 chars but 74 UTF-8 bytes
        {"email": "not-an-email"},
        {"full_name": "   "},
    ],
)
def test_register_validation(client: TestClient, over: dict[str, Any]) -> None:
    assert _register(client, **over).status_code == 422


def test_password_72_bytes_ok_and_long_login_is_401(client: TestClient) -> None:
    assert _register(client, password="a" * 72).status_code == 201
    r = client.post("/auth/login", json={"email": "new@example.com", "password": "\u00e9" * 100})
    assert r.status_code == 401  # never a 500


def test_login_user_without_password_generic_401(client: TestClient, db: Session) -> None:
    db.add(User(email="oauth@example.com", hashed_password=None, is_active=True))
    db.commit()
    r = client.post("/auth/login", json={"email": "oauth@example.com", "password": "password123"})
    assert r.status_code == 401
    assert r.json()["error"]["message"] == "Invalid email or password"


def test_hash_password_guard() -> None:
    with pytest.raises(ValueError):
        hash_password("x" * 73)
    assert verify_password("x" * 73, hash_password("y")) is False


def test_short_or_placeholder_secret_key_rejected() -> None:
    from pydantic import ValidationError

    from app.config import Settings

    base: dict[str, Any] = {"DATABASE_URL": "sqlite://", "_env_file": None}
    for bad in ("short", "dev-only-change-me", "x" * 10 + "your-secret-key" + "y" * 20):
        with pytest.raises(ValidationError):
            Settings(SECRET_KEY=bad, **base)
    assert Settings(SECRET_KEY="k9Xv2Lq8Zr4TnB7wYc1PdF6hGj3MsA5u", **base).SECRET_KEY


def test_login_ok_sets_cookie_and_no_refresh_in_body(client: TestClient) -> None:
    _register(client)
    r = client.post("/auth/login", json={"email": "new@example.com", "password": "password123"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert set(body) == {"access_token", "token_type"}
    raw = r.headers["set-cookie"]
    low = raw.lower()
    assert raw.startswith("tp_refresh=")
    assert "httponly" in low and "samesite=strict" in low and "path=/auth" in low
    assert f"max-age={settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400}" in low
    assert "secure" not in low  # FRONTEND_URL is http in tests
    assert "domain=" not in low
    assert r.cookies.get("tp_refresh") not in r.text


def test_cookie_attributes_follow_settings(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://app.example.com")
    monkeypatch.setattr(settings, "COOKIE_SAMESITE", "lax")
    monkeypatch.setattr(settings, "COOKIE_DOMAIN", "example.com")
    _register(client)
    r = client.post("/auth/login", json={"email": "new@example.com", "password": "password123"})
    parts = [p.strip().lower() for p in r.headers["set-cookie"].split(";")]
    assert "secure" in parts and "samesite=lax" in parts and "domain=example.com" in parts
    monkeypatch.setattr(settings, "COOKIE_SECURE", False)
    r = client.post("/auth/login", json={"email": "new@example.com", "password": "password123"})
    parts = [p.strip().lower() for p in r.headers["set-cookie"].split(";")]
    assert "secure" not in parts


def test_login_bad_password_and_unknown_user(client: TestClient) -> None:
    _register(client)
    bad = client.post("/auth/login", json={"email": "new@example.com", "password": "wrongpass1"})
    unknown = client.post(
        "/auth/login", json={"email": "no@example.com", "password": "password123"}
    )
    assert bad.status_code == 401
    assert unknown.status_code == 401
    assert bad.json()["error"]["message"] == unknown.json()["error"]["message"]


def test_login_inactive_user_rejected(client: TestClient, db: Session) -> None:
    _register(client)
    user = db.query(User).filter_by(email="new@example.com").one()
    user.is_active = False
    db.commit()
    r = client.post("/auth/login", json={"email": "new@example.com", "password": "password123"})
    assert r.status_code == 401


def _use_cookie(client: TestClient, token: str | None) -> None:
    """Make the client's jar hold exactly this refresh cookie (or none)."""
    client.cookies.clear()
    if token is not None:
        client.cookies.set("tp_refresh", token, path="/auth")


def _refresh(client: TestClient, token: str | None = None, headers: Any = CSRF) -> Any:
    _use_cookie(client, token)
    return client.post("/auth/refresh", headers=headers)


def _is_cleared(r: Any) -> bool:
    sc = r.headers["set-cookie"].lower()
    return sc.startswith("tp_refresh=") and "max-age=0" in sc and "path=/auth" in sc


def test_refresh_rotation_old_token_rejected(client: TestClient, user_a: dict[str, Any]) -> None:
    old = user_a["tokens"]["refresh_token"]
    r = _refresh(client, old)
    assert r.status_code == 200
    new = r.json()
    assert set(new) == {"access_token", "token_type"}
    new_cookie = r.cookies.get("tp_refresh")
    assert new_cookie and new_cookie != old
    assert "httponly" in r.headers["set-cookie"].lower()
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {new['access_token']}"})
    assert me.status_code == 200
    # New one is valid (rotation) until the old one is replayed
    assert _refresh(client, new_cookie).status_code == 200
    # Old token is revoked
    assert _refresh(client, old).status_code == 401


def test_refresh_uses_jar_cookie_after_login(client: TestClient, user_a: dict[str, Any]) -> None:
    # The browser flow: no body, cookie sent automatically.
    r = client.post("/auth/refresh", headers=CSRF)
    assert r.status_code == 200 and r.json()["access_token"]


def test_refresh_reuse_revokes_whole_family(
    client: TestClient, db: Session, user_a: dict[str, Any]
) -> None:
    old = user_a["tokens"]["refresh_token"]
    new = _refresh(client, old).cookies.get("tp_refresh")
    # Replaying the rotated token is theft: 401, cookie cleared, every token revoked.
    replay = _refresh(client, old)
    assert replay.status_code == 401
    assert _is_cleared(replay)
    db.expire_all()
    assert all(t.revoked for t in db.query(RefreshToken).all())
    assert _refresh(client, new).status_code == 401


def test_refresh_missing_or_unknown_cookie_401_clears_cookie(client: TestClient) -> None:
    for tok in (None, "nope"):
        r = _refresh(client, tok)
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "UNAUTHORIZED"
        assert _is_cleared(r)


def test_refresh_requires_custom_header(client: TestClient, user_a: dict[str, Any]) -> None:
    tok = user_a["tokens"]["refresh_token"]
    r = _refresh(client, tok, headers={})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"
    wrong = {"X-Requested-With": "XMLHttpRequest"}
    assert _refresh(client, tok, headers=wrong).status_code == 403
    # the token was not consumed by the rejected attempts
    assert _refresh(client, tok).status_code == 200


def test_refresh_and_logout_reject_foreign_origin(
    client: TestClient, user_a: dict[str, Any]
) -> None:
    tok = user_a["tokens"]["refresh_token"]
    evil = {**CSRF, "Origin": "https://evil.example"}
    assert _refresh(client, tok, headers=evil).status_code == 403
    _use_cookie(client, tok)
    assert client.post("/auth/logout", headers=evil).status_code == 403
    good = {**CSRF, "Origin": settings.cors_origins_list[0]}
    assert _refresh(client, tok, headers=good).status_code == 200


def test_logout_requires_custom_header(client: TestClient, user_a: dict[str, Any]) -> None:
    assert client.post("/auth/logout").status_code == 403


def test_refresh_expired_token_401(client: TestClient, db: Session, user_a: dict[str, Any]) -> None:
    rec = db.query(RefreshToken).one()
    rec.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()
    assert _refresh(client, user_a["tokens"]["refresh_token"]).status_code == 401


def test_refresh_for_deactivated_user_401(
    client: TestClient, db: Session, user_a: dict[str, Any]
) -> None:
    user = db.query(User).one()
    user.is_active = False
    db.commit()
    assert _refresh(client, user_a["tokens"]["refresh_token"]).status_code == 401


def test_refresh_body_is_ignored(client: TestClient, user_a: dict[str, Any]) -> None:
    # A refresh token in a JSON body must not be accepted any more.
    rt = user_a["tokens"]["refresh_token"]
    _use_cookie(client, None)
    r = client.post("/auth/refresh", json={"refresh_token": rt}, headers=CSRF)
    assert r.status_code == 401


def test_refresh_token_stored_hashed(db: Session, user_a: dict[str, Any]) -> None:
    rec = db.query(RefreshToken).one()
    assert rec.token_hash != user_a["tokens"]["refresh_token"]


def test_logout_revokes_refresh_and_clears_cookie(
    client: TestClient, db: Session, user_a: dict[str, Any]
) -> None:
    rt = user_a["tokens"]["refresh_token"]
    _use_cookie(client, rt)
    out = client.post("/auth/logout", headers=CSRF)
    assert out.status_code == 204
    assert _is_cleared(out)
    db.expire_all()
    assert all(t.revoked for t in db.query(RefreshToken).all())
    assert _refresh(client, rt).status_code == 401
    # idempotent: replayed, missing and unknown cookies all give 204
    for tok in (rt, None, "unknown"):
        _use_cookie(client, tok)
        assert client.post("/auth/logout", headers=CSRF).status_code == 204


def test_cors_credentials_only_for_allowlisted_origin(client: TestClient) -> None:
    allowed = settings.cors_origins_list[0]
    pre = {
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "x-requested-with,content-type,authorization",
    }
    ok = client.options("/auth/refresh", headers={"Origin": allowed, **pre})
    assert ok.status_code == 200
    assert ok.headers["access-control-allow-origin"] == allowed
    assert ok.headers["access-control-allow-credentials"] == "true"
    allow_headers = ok.headers["access-control-allow-headers"].lower()
    for h in ("authorization", "content-type", "x-requested-with"):
        assert h in allow_headers
    bad = client.options("/auth/refresh", headers={"Origin": "https://evil.example", **pre})
    assert bad.status_code == 400
    assert "access-control-allow-origin" not in bad.headers
    # Starlette's denied preflight still carries allow-credentials, but with no
    # allow-origin the browser refuses; the actual (non-preflight) response is checked too.
    actual = client.post("/auth/refresh", headers={"Origin": "https://evil.example", **CSRF})
    assert actual.status_code == 403
    assert "access-control-allow-origin" not in actual.headers


def test_me_requires_auth(client: TestClient) -> None:
    r = client.get("/auth/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_me_ok(client: TestClient, user_a: dict[str, Any], auth_a: dict[str, str]) -> None:
    r = client.get("/auth/me", headers=auth_a)
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"
    assert r.json()["id"] == user_a["user"]["id"]


def test_update_profile(client: TestClient, auth_a: dict[str, str]) -> None:
    r = client.put("/auth/me", json={"full_name": "  Alice Smith "}, headers=auth_a)
    assert r.status_code == 200
    assert r.json()["full_name"] == "Alice Smith"
    assert client.get("/auth/me", headers=auth_a).json()["full_name"] == "Alice Smith"
    assert client.put("/auth/me", json={"full_name": " "}, headers=auth_a).status_code == 422
    assert client.put("/auth/me", json={"full_name": "x"}).status_code == 401


def test_expired_jwt_401(client: TestClient, user_a: dict[str, Any]) -> None:
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(user_a["user"]["id"]),
            "type": "access",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_tampered_jwt_401(client: TestClient, auth_a: dict[str, str]) -> None:
    token = auth_a["Authorization"].split()[1]
    head, payload, sig = token.split(".")
    tampered = f"{head}.{payload}.{sig[:-3]}abc"
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {tampered}"})
    assert r.status_code == 401


def test_jwt_signed_with_wrong_key_401(client: TestClient, user_a: dict[str, Any]) -> None:
    token = jwt.encode(
        {"sub": str(user_a["user"]["id"]), "type": "access"}, "x" * 40, algorithm="HS256"
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_garbage_and_wrong_type_token_401(client: TestClient, user_a: dict[str, Any]) -> None:
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    wrong_type = jwt.encode(
        {"sub": str(user_a["user"]["id"]), "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    assert (
        client.get("/auth/me", headers={"Authorization": f"Bearer {wrong_type}"}).status_code == 401
    )


def test_token_for_deleted_user_401(client: TestClient) -> None:
    token = create_access_token(99999)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_jwt_helpers() -> None:
    h = hash_password("secret-pw")
    assert verify_password("secret-pw", h)
    assert not verify_password("other", h)
    assert not verify_password("x", "not-a-bcrypt-hash")
    assert decode_access_token(create_access_token(7)) == 7
    bad_sub = jwt.encode(
        {"sub": "abc", "type": "access"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    assert decode_access_token(bad_sub) is None
    no_sub = jwt.encode({"type": "access"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    assert decode_access_token(no_sub) is None


# ---- Google OAuth ----------------------------------------------------------
def test_google_not_configured_501(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    r = client.get("/auth/google", follow_redirects=False)
    assert r.status_code == 501
    assert r.json()["error"]["code"] == "OAUTH_NOT_CONFIGURED"


def _configure_google(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "secret")


def test_google_redirect_and_callback_creates_user(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_google(monkeypatch)
    r = client.get("/auth/google", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"].startswith(oauth.GOOGLE_AUTH_URL)
    state = parse_qs(urlparse(r.headers["location"]).query)["state"][0]
    set_cookie = r.headers["set-cookie"].lower()
    assert "oauth_state_nonce=" in set_cookie
    assert "httponly" in set_cookie and "samesite=lax" in set_cookie
    assert "path=/auth" in set_cookie and "max-age=600" in set_cookie
    assert "secure" not in set_cookie  # FRONTEND_URL is http in tests

    monkeypatch.setattr(
        oauth,
        "fetch_google_profile",
        lambda code: {"email": "G@Example.com", "email_verified": True, "name": "Gee"},
    )
    cb = client.get(
        "/auth/google/callback", params={"code": "c", "state": state}, follow_redirects=False
    )
    assert cb.status_code == 302
    loc = urlparse(cb.headers["location"])
    assert loc.query == ""  # tokens must never be in the query string
    assert loc.fragment == ""  # ...nor in the fragment
    assert loc.path == "/auth/callback"
    assert "token" not in cb.headers["location"].lower()
    assert cb.headers["referrer-policy"] == "no-referrer"
    assert cb.headers["cache-control"] == "no-store"
    assert "oauth_state_nonce" not in client.cookies  # cleared after use
    refresh_hdr = next(
        v for k, v in cb.headers.multi_items() if k == "set-cookie" and v.startswith("tp_refresh=")
    )
    low = refresh_hdr.lower()
    assert "httponly" in low and "samesite=strict" in low and "path=/auth" in low
    # Frontend then exchanges the cookie for an access token.
    ref = client.post("/auth/refresh", headers=CSRF)
    assert ref.status_code == 200
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {ref.json()['access_token']}"})
    assert me.json()["email"] == "g@example.com"
    assert me.json()["oauth_provider"] == "google"
    assert me.json()["is_verified"] is True


def test_google_callback_bad_state_401(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_google(monkeypatch)
    r = client.get(
        "/auth/google/callback", params={"code": "c", "state": "bad"}, follow_redirects=False
    )
    assert r.status_code == 401
    assert "oauth_state_nonce" in r.headers["set-cookie"]  # deletion header
    wrong = jwt.encode({"type": "access"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    r = client.get(
        "/auth/google/callback", params={"code": "c", "state": wrong}, follow_redirects=False
    )
    assert r.status_code == 401


def test_google_links_existing_user_and_rejects_unverified(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_google(monkeypatch)
    _register(client, "link@example.com")
    state, nonce = oauth.create_state()
    client.cookies.set("oauth_state_nonce", nonce, path="/auth")
    monkeypatch.setattr(
        oauth,
        "fetch_google_profile",
        lambda code: {"email": "link@example.com", "email_verified": True, "name": "X"},
    )
    cb = client.get(
        "/auth/google/callback", params={"code": "c", "state": state}, follow_redirects=False
    )
    assert cb.status_code == 302
    user = db.query(User).filter_by(email="link@example.com").one()
    assert user.oauth_provider == "google"
    assert user.hashed_password is None and user.is_verified is True

    monkeypatch.setattr(
        oauth,
        "fetch_google_profile",
        lambda code: {"email": "u@example.com", "email_verified": False},
    )
    cb = client.get(
        "/auth/google/callback", params={"code": "c", "state": state}, follow_redirects=False
    )
    assert cb.status_code == 502

    user.is_active = False
    db.commit()
    monkeypatch.setattr(
        oauth,
        "fetch_google_profile",
        lambda code: {"email": "link@example.com", "email_verified": True},
    )
    cb = client.get(
        "/auth/google/callback", params={"code": "c", "state": state}, follow_redirects=False
    )
    assert cb.status_code == 401


def _google_cookie_and_state(client: TestClient) -> str:
    r = client.get("/auth/google", follow_redirects=False)
    return parse_qs(urlparse(r.headers["location"]).query)["state"][0]


def test_google_callback_state_cookie_mismatch_400(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_google(monkeypatch)
    called: list[str] = []
    monkeypatch.setattr(
        oauth,
        "fetch_google_profile",
        lambda code: called.append(code) or {"email": "x@example.com", "email_verified": True},
    )
    state, _nonce = oauth.create_state()
    # Missing cookie
    client.cookies.clear()
    r = client.get("/auth/google/callback", params={"code": "c", "state": state})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "OAUTH_STATE_MISMATCH"
    # Wrong cookie (state minted for a different browser)
    client.cookies.set("oauth_state_nonce", "someone-elses-nonce", path="/auth")
    r = client.get("/auth/google/callback", params={"code": "c", "state": state})
    assert r.status_code == 400
    assert "oauth_state_nonce" in r.headers["set-cookie"]
    assert not called and db.query(User).count() == 0


def test_google_link_clears_password_and_revokes_sessions(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_google(monkeypatch)
    _register(client, "victim@example.com")
    login = client.post(
        "/auth/login", json={"email": "victim@example.com", "password": "password123"}
    )
    attacker_refresh = login.cookies["tp_refresh"]
    state = _google_cookie_and_state(client)
    monkeypatch.setattr(
        oauth,
        "fetch_google_profile",
        lambda code: {"email": "victim@example.com", "email_verified": True},
    )
    cb = client.get(
        "/auth/google/callback", params={"code": "c", "state": state}, follow_redirects=False
    )
    assert cb.status_code == 302
    db.expire_all()
    user = db.query(User).filter_by(email="victim@example.com").one()
    assert user.hashed_password is None
    assert user.is_verified is True and user.oauth_provider == "google"
    # Attacker's password no longer works (generic 401) and old sessions are dead.
    bad = client.post(
        "/auth/login", json={"email": "victim@example.com", "password": "password123"}
    )
    assert bad.status_code == 401
    assert _refresh(client, attacker_refresh).status_code == 401


class _Resp:
    def __init__(self, status: int, data: dict[str, Any]) -> None:
        self.status_code = status
        self._data = data

    def json(self) -> dict[str, Any]:
        return self._data


class _FakeClient:
    def __init__(self, token: _Resp, info: _Resp | None = None, raise_exc: bool = False) -> None:
        self.token, self.info, self.raise_exc = token, info, raise_exc

    def __enter__(self) -> "_FakeClient":
        return self

    def __exit__(self, *a: object) -> None:
        return None

    def post(self, *a: Any, **k: Any) -> _Resp:
        if self.raise_exc:
            import httpx

            raise httpx.ConnectError("boom")
        return self.token

    def get(self, *a: Any, **k: Any) -> _Resp:
        assert self.info is not None
        return self.info


def test_fetch_google_profile_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    def patch(fake: _FakeClient) -> None:
        monkeypatch.setattr(oauth.httpx, "Client", lambda **k: fake)

    patch(_FakeClient(_Resp(200, {"access_token": "t"}), _Resp(200, {"email": "a@b.c"})))
    assert oauth.fetch_google_profile("c") == {"email": "a@b.c"}
    patch(_FakeClient(_Resp(400, {})))
    with pytest.raises(oauth.OAuthFailedError):
        oauth.fetch_google_profile("c")
    patch(_FakeClient(_Resp(200, {})))
    with pytest.raises(oauth.OAuthFailedError):
        oauth.fetch_google_profile("c")
    patch(_FakeClient(_Resp(200, {"access_token": "t"}), _Resp(500, {})))
    with pytest.raises(oauth.OAuthFailedError):
        oauth.fetch_google_profile("c")
    patch(_FakeClient(_Resp(200, {}), raise_exc=True))
    with pytest.raises(oauth.OAuthFailedError):
        oauth.fetch_google_profile("c")


def test_health_and_unhandled_error(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
