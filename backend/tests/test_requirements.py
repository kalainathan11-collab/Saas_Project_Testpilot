"""Requirements module tests."""

from fastapi.testclient import TestClient

from tests.conftest import Factory


def test_requires_auth(client: TestClient) -> None:
    assert client.get("/api/requirements").status_code == 401


def test_crud_and_test_case_count(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_requirement: Factory,
    make_case: Factory,
) -> None:
    p = make_project(auth_a)
    r = make_requirement(auth_a, p["id"], title="  Login works ", priority="High")
    assert r["title"] == "Login works"
    assert r["priority"] == "High"
    assert r["status"] == "Proposed"
    assert r["test_case_count"] == 0

    c1 = make_case(auth_a, p["id"], requirement_id=r["id"], title="TC one")
    make_case(auth_a, p["id"], requirement_id=r["id"], title="TC two")
    make_case(auth_a, p["id"], title="unlinked")

    one = client.get(f"/api/requirements/{r['id']}", headers=auth_a).json()
    assert one["test_case_count"] == 2
    assert {tc["title"] for tc in one["test_cases"]} == {"TC one", "TC two"}
    assert set(one["test_cases"][0]) == {"id", "title", "status"}

    listed = client.get("/api/requirements", headers=auth_a).json()
    assert listed[0]["test_case_count"] == 2

    upd = client.put(
        f"/api/requirements/{r['id']}",
        json={
            "title": "Login v2",
            "description": "x",
            "priority": "Critical",
            "status": "Approved",
        },
        headers=auth_a,
    )
    assert upd.status_code == 200
    assert upd.json()["title"] == "Login v2"
    assert upd.json()["status"] == "Approved"
    assert upd.json()["test_case_count"] == 2

    # Deleting detaches linked test cases (does not delete them)
    assert client.delete(f"/api/requirements/{r['id']}", headers=auth_a).status_code == 204
    assert client.get(f"/api/requirements/{r['id']}", headers=auth_a).status_code == 404
    tc = client.get(f"/api/testcases/{c1['id']}", headers=auth_a).json()
    assert tc["requirement_id"] is None


def test_filters(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_requirement: Factory,
) -> None:
    p1 = make_project(auth_a)
    p2 = make_project(auth_a)
    make_requirement(auth_a, p1["id"], title="Pay by card", priority="High")
    make_requirement(auth_a, p1["id"], title="Export", priority="Low", status="Approved")
    make_requirement(auth_a, p2["id"], title="Other", description="searchable words")

    def titles(qs: str) -> list[str]:
        return [x["title"] for x in client.get(f"/api/requirements?{qs}", headers=auth_a).json()]

    assert titles(f"project_id={p1['id']}") == ["Export", "Pay by card"]
    assert titles("priority=High") == ["Pay by card"]
    assert titles("status=Approved") == ["Export"]
    assert titles("q=CARD") == ["Pay by card"]
    assert titles("q=searchable") == ["Other"]
    assert titles("limit=1&offset=1") == ["Export"]
    assert client.get("/api/requirements?priority=Nope", headers=auth_a).status_code == 422


def test_validation(client: TestClient, auth_a: dict[str, str], make_project: Factory) -> None:
    p = make_project(auth_a)
    r = client.post(
        "/api/requirements", json={"project_id": p["id"], "title": "   "}, headers=auth_a
    )
    assert r.status_code == 422
    r = client.post("/api/requirements", json={"title": "no project"}, headers=auth_a)
    assert r.status_code == 422


def test_other_users_project_rejected(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
) -> None:
    pb = make_project(auth_b)
    r = client.post(
        "/api/requirements", json={"project_id": pb["id"], "title": "sneaky"}, headers=auth_a
    )
    assert r.status_code == 404
    assert client.get("/api/requirements", headers=auth_b).json() == []
    assert (
        client.post(
            "/api/requirements", json={"project_id": 99999, "title": "x"}, headers=auth_a
        ).status_code
        == 404
    )


def test_cross_user_isolation(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
    make_requirement: Factory,
) -> None:
    p = make_project(auth_a)
    req = make_requirement(auth_a, p["id"])
    rid = req["id"]
    assert client.get("/api/requirements", headers=auth_b).json() == []
    assert client.get(f"/api/requirements?project_id={p['id']}", headers=auth_b).json() == []
    assert client.get(f"/api/requirements/{rid}", headers=auth_b).status_code == 404
    r = client.put(
        f"/api/requirements/{rid}",
        json={"title": "hack", "priority": "Low", "status": "Proposed"},
        headers=auth_b,
    )
    assert r.status_code == 404
    assert client.delete(f"/api/requirements/{rid}", headers=auth_b).status_code == 404
    assert client.get(f"/api/requirements/{rid}", headers=auth_a).json()["title"] == req["title"]
