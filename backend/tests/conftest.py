"""Test configuration: provide required settings before app import, isolated SQLite DB."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "k9Xv2Lq8Zr4TnB7wYc1PdF6hGj3MsA5uEo0RiVx")

from collections.abc import Callable, Generator  # noqa: E402
from typing import Any  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402,F401  (registers all tables on Base.metadata)
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.rate_limit import limiter  # noqa: E402

PASSWORD = "password123"


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> Generator[None, None, None]:
    """Fresh rate-limit counters per test; the suite registers many users from one IP."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def engine() -> Generator[Engine, None, None]:
    """Fresh in-memory SQLite database per test (FK enforcement ON, like Postgres)."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def _fk_on(dbapi_conn: Any, _record: Any) -> None:
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine: Engine) -> Generator[Session, None, None]:
    session = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    yield session
    session.close()


@pytest.fixture
def client(engine: Engine) -> Generator[TestClient, None, None]:
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def _get_db() -> Generator[Session, None, None]:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _register_and_login(client: TestClient, email: str, name: str) -> dict[str, Any]:
    r = client.post(
        "/auth/register", json={"email": email, "password": PASSWORD, "full_name": name}
    )
    assert r.status_code == 201, r.text
    login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.text
    tokens = login.json()
    # The refresh token only exists as an HttpOnly cookie; keep it for replay tests.
    tokens["refresh_token"] = login.cookies.get("tp_refresh")
    return {
        "user": r.json(),
        "tokens": tokens,
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"},
    }


@pytest.fixture
def user_a(client: TestClient) -> dict[str, Any]:
    return _register_and_login(client, "alice@example.com", "Alice")


@pytest.fixture
def user_b(client: TestClient) -> dict[str, Any]:
    return _register_and_login(client, "bob@example.com", "Bob")


@pytest.fixture
def auth_a(user_a: dict[str, Any]) -> dict[str, str]:
    return user_a["headers"]


@pytest.fixture
def auth_b(user_b: dict[str, Any]) -> dict[str, str]:
    return user_b["headers"]


# ---- factory helpers -------------------------------------------------------
Factory = Callable[..., dict[str, Any]]


@pytest.fixture
def make_project(client: TestClient) -> Factory:
    counter = {"n": 0}

    def _make(headers: dict[str, str], **over: Any) -> dict[str, Any]:
        counter["n"] += 1
        body = {"name": f"Project {counter['n']}", "key": f"P{counter['n']}"}
        body.update(over)
        r = client.post("/api/projects", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _make


@pytest.fixture
def make_requirement(client: TestClient) -> Factory:
    def _make(headers: dict[str, str], project_id: int, **over: Any) -> dict[str, Any]:
        body = {"project_id": project_id, "title": "Req"}
        body.update(over)
        r = client.post("/api/requirements", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _make


@pytest.fixture
def make_case(client: TestClient) -> Factory:
    def _make(headers: dict[str, str], project_id: int, **over: Any) -> dict[str, Any]:
        body = {"project_id": project_id, "title": "Case"}
        body.update(over)
        r = client.post("/api/testcases", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _make


@pytest.fixture
def make_run(client: TestClient) -> Factory:
    def _make(headers: dict[str, str], project_id: int, **over: Any) -> dict[str, Any]:
        body = {"project_id": project_id, "name": "Run"}
        body.update(over)
        r = client.post("/api/testruns", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _make


@pytest.fixture
def make_defect(client: TestClient) -> Factory:
    def _make(headers: dict[str, str], project_id: int, **over: Any) -> dict[str, Any]:
        body = {"project_id": project_id, "title": "Bug"}
        body.update(over)
        r = client.post("/api/defects", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _make
