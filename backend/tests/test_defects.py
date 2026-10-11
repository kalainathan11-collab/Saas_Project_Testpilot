"""Defects module tests."""

from fastapi.testclient import TestClient

from tests.conftest import Factory


def test_requires_auth(client: TestClient) -> None:
    assert client.get("/api/defects").status_code == 401


def test_crud(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_case: Factory,
    make_defect: Factory,
) -> None:
    p = make_project(auth_a)
    case = make_case(auth_a, p["id"])
    d = make_defect(
        auth_a,
        p["id"],
        title="Crash on save",
        test_case_id=case["id"],
        severity="Critical",
        assignee="dev1",
        description="stack trace",
    )
    assert d["severity"] == "Critical"
    assert d["status"] == "Open"
    assert d["test_case_id"] == case["id"]

    got = client.get(f"/api/defects/{d['id']}", headers=auth_a)
    assert got.status_code == 200 and got.json()["title"] == "Crash on save"

    upd = client.put(
        f"/api/defects/{d['id']}",
        json={
            "project_id": p["id"],
            "title": "Crash on save (fixed)",
            "severity": "Minor",
            "status": "Resolved",
            "test_case_id": None,
        },
        headers=auth_a,
    )
    assert upd.status_code == 200
    out = upd.json()
    assert out["status"] == "Resolved" and out["severity"] == "Minor"
    assert out["test_case_id"] is None and out["assignee"] is None

    assert client.delete(f"/api/defects/{d['id']}", headers=auth_a).status_code == 204
    assert client.get(f"/api/defects/{d['id']}", headers=auth_a).status_code == 404


def test_defaults_and_validation(
    client: TestClient, auth_a: dict[str, str], make_project: Factory, make_defect: Factory
) -> None:
    p = make_project(auth_a)
    d = make_defect(auth_a, p["id"])
    assert (d["severity"], d["status"]) == ("Major", "Open")
    for bad in (
        {"project_id": p["id"], "title": ""},
        {"project_id": p["id"], "title": "t", "severity": "Huge"},
        {"project_id": p["id"], "title": "t", "status": "Nope"},
        {"title": "t"},
    ):
        assert client.post("/api/defects", json=bad, headers=auth_a).status_code == 422


def test_filters(
    client: TestClient, auth_a: dict[str, str], make_project: Factory, make_defect: Factory
) -> None:
    p1, p2 = make_project(auth_a), make_project(auth_a)
    make_defect(auth_a, p1["id"], title="Login broken", severity="Blocker")
    make_defect(auth_a, p1["id"], title="Typo", severity="Minor", status="Closed")
    make_defect(auth_a, p2["id"], title="Slow", description="takes forever")

    def titles(qs: str) -> list[str]:
        return [x["title"] for x in client.get(f"/api/defects?{qs}", headers=auth_a).json()]

    assert titles("") == ["Slow", "Typo", "Login broken"]
    assert titles(f"project_id={p1['id']}") == ["Typo", "Login broken"]
    assert titles("severity=Blocker") == ["Login broken"]
    assert titles("status=Closed") == ["Typo"]
    assert titles("q=forever") == ["Slow"]
    assert titles("q=LOGIN") == ["Login broken"]
    assert titles("limit=1&offset=2") == ["Login broken"]
    assert client.get("/api/defects?severity=Huge", headers=auth_a).status_code == 422


def test_foreign_references_rejected(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
    make_case: Factory,
    make_defect: Factory,
) -> None:
    pa1, pa2 = make_project(auth_a), make_project(auth_a)
    pb = make_project(auth_b)
    case_b = make_case(auth_b, pb["id"])
    case_a2 = make_case(auth_a, pa2["id"])

    r = client.post("/api/defects", json={"project_id": pb["id"], "title": "x"}, headers=auth_a)
    assert r.status_code == 404
    r = client.post(
        "/api/defects",
        json={"project_id": pa1["id"], "title": "x", "test_case_id": case_b["id"]},
        headers=auth_a,
    )
    assert r.status_code == 404
    # own test case but different project
    r = client.post(
        "/api/defects",
        json={"project_id": pa1["id"], "title": "x", "test_case_id": case_a2["id"]},
        headers=auth_a,
    )
    assert r.status_code == 404

    d = make_defect(auth_a, pa1["id"])
    r = client.put(
        f"/api/defects/{d['id']}",
        json={"project_id": pa1["id"], "title": "x", "test_case_id": case_b["id"]},
        headers=auth_a,
    )
    assert r.status_code == 404
    r = client.put(
        f"/api/defects/{d['id']}",
        json={"project_id": pb["id"], "title": "x"},
        headers=auth_a,
    )
    assert r.status_code == 404


def test_deleting_test_case_keeps_defect(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_case: Factory,
    make_defect: Factory,
) -> None:
    p = make_project(auth_a)
    case = make_case(auth_a, p["id"])
    d = make_defect(auth_a, p["id"], test_case_id=case["id"])
    assert client.delete(f"/api/testcases/{case['id']}", headers=auth_a).status_code == 204
    got = client.get(f"/api/defects/{d['id']}", headers=auth_a).json()
    assert got["test_case_id"] is None


def test_cross_user_isolation(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
    make_defect: Factory,
) -> None:
    p = make_project(auth_a)
    d = make_defect(auth_a, p["id"])
    did = d["id"]
    assert client.get("/api/defects", headers=auth_b).json() == []
    assert client.get(f"/api/defects?project_id={p['id']}", headers=auth_b).json() == []
    assert client.get(f"/api/defects/{did}", headers=auth_b).status_code == 404
    r = client.put(
        f"/api/defects/{did}", json={"project_id": p["id"], "title": "hack"}, headers=auth_b
    )
    assert r.status_code == 404
    assert client.delete(f"/api/defects/{did}", headers=auth_b).status_code == 404
    assert client.get(f"/api/defects/{did}", headers=auth_a).json()["title"] == d["title"]
