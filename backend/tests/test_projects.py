"""Projects module tests."""

from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import Factory


def test_requires_auth(client: TestClient) -> None:
    assert client.get("/api/projects").status_code == 401
    assert client.post("/api/projects", json={"name": "n", "key": "k"}).status_code == 401


def test_create_get_update_delete(
    client: TestClient, auth_a: dict[str, str], make_project: Factory
) -> None:
    p = make_project(auth_a, name="Alpha", key="alp", description="d")
    assert p["key"] == "ALP"  # uppercased
    assert p["status"] == "Active"
    assert p["owner"] == "Alice"

    got = client.get(f"/api/projects/{p['id']}", headers=auth_a)
    assert got.status_code == 200
    assert got.json()["counts"] == {
        "requirements": 0,
        "test_cases": 0,
        "test_runs": 0,
        "defects": 0,
    }

    upd = client.put(
        f"/api/projects/{p['id']}",
        json={"name": "Beta", "key": "bet", "description": None, "status": "On Hold"},
        headers=auth_a,
    )
    assert upd.status_code == 200
    assert upd.json()["name"] == "Beta"
    assert upd.json()["key"] == "BET"
    assert upd.json()["status"] == "On Hold"

    assert client.delete(f"/api/projects/{p['id']}", headers=auth_a).status_code == 204
    assert client.get(f"/api/projects/{p['id']}", headers=auth_a).status_code == 404
    assert client.delete(f"/api/projects/{p['id']}", headers=auth_a).status_code == 404


def test_duplicate_key_409_create_and_update(
    client: TestClient, auth_a: dict[str, str], make_project: Factory
) -> None:
    make_project(auth_a, key="DUP")
    r = client.post("/api/projects", json={"name": "x", "key": "dup"}, headers=auth_a)
    assert r.status_code == 409
    other = make_project(auth_a, key="OTHER")
    r = client.put(f"/api/projects/{other['id']}", json={"name": "x", "key": "DUP"}, headers=auth_a)
    assert r.status_code == 409
    # updating with its own key is fine
    r = client.put(
        f"/api/projects/{other['id']}", json={"name": "x2", "key": "other"}, headers=auth_a
    )
    assert r.status_code == 200


def test_same_key_allowed_for_different_users(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
) -> None:
    make_project(auth_a, key="SAME")
    make_project(auth_b, key="SAME")


def test_validation_errors(client: TestClient, auth_a: dict[str, str]) -> None:
    assert (
        client.post("/api/projects", json={"name": " ", "key": "K"}, headers=auth_a).status_code
        == 422
    )
    assert client.post("/api/projects", json={"name": "n"}, headers=auth_a).status_code == 422
    r = client.post(
        "/api/projects", json={"name": "n", "key": "K", "status": "Bogus"}, headers=auth_a
    )
    assert r.status_code == 422


def test_filters_and_pagination(
    client: TestClient, auth_a: dict[str, str], make_project: Factory
) -> None:
    make_project(auth_a, name="Checkout", key="CHK")
    make_project(auth_a, name="Billing", key="BIL", status="Archived", description="invoices")
    make_project(auth_a, name="Search", key="SRC")
    all_ = client.get("/api/projects", headers=auth_a).json()
    assert [p["key"] for p in all_] == ["SRC", "BIL", "CHK"]  # newest first
    assert [p["key"] for p in client.get("/api/projects?q=invoice", headers=auth_a).json()] == [
        "BIL"
    ]
    assert [p["key"] for p in client.get("/api/projects?q=chk", headers=auth_a).json()] == ["CHK"]
    arch = client.get("/api/projects?status=Archived", headers=auth_a).json()
    assert [p["key"] for p in arch] == ["BIL"]
    page = client.get("/api/projects?limit=1&offset=1", headers=auth_a).json()
    assert [p["key"] for p in page] == ["BIL"]
    assert client.get("/api/projects?limit=501", headers=auth_a).status_code == 422
    assert client.get("/api/projects?status=Nope", headers=auth_a).status_code == 422


def test_counts_and_cascade_delete(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_requirement: Factory,
    make_case: Factory,
    make_run: Factory,
    make_defect: Factory,
) -> None:
    p = make_project(auth_a)
    req = make_requirement(auth_a, p["id"])
    case = make_case(auth_a, p["id"], requirement_id=req["id"])
    run = make_run(auth_a, p["id"])
    client.put(
        f"/api/testruns/{run['id']}/results/{case['id']}",
        json={"status": "Passed"},
        headers=auth_a,
    )
    make_defect(auth_a, p["id"], test_case_id=case["id"])
    counts = client.get(f"/api/projects/{p['id']}", headers=auth_a).json()["counts"]
    assert counts == {"requirements": 1, "test_cases": 1, "test_runs": 1, "defects": 1}

    assert client.delete(f"/api/projects/{p['id']}", headers=auth_a).status_code == 204
    for path in ("requirements", "testcases", "testruns", "defects"):
        assert client.get(f"/api/{path}", headers=auth_a).json() == []


def test_cross_user_isolation(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
) -> None:
    p = make_project(auth_a, key="PRIV")
    pid = p["id"]
    assert client.get("/api/projects", headers=auth_b).json() == []
    assert client.get(f"/api/projects/{pid}", headers=auth_b).status_code == 404
    r = client.put(f"/api/projects/{pid}", json={"name": "hack", "key": "H"}, headers=auth_b)
    assert r.status_code == 404
    assert client.delete(f"/api/projects/{pid}", headers=auth_b).status_code == 404
    # still intact for owner
    mine: Any = client.get(f"/api/projects/{pid}", headers=auth_a).json()
    assert mine["name"] == p["name"]
