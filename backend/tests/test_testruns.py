"""Test runs module tests."""

from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import Factory


def _result(
    client: TestClient,
    headers: dict[str, str],
    run_id: int,
    case_id: int,
    status: str = "Passed",
    comment: str | None = None,
) -> Any:
    return client.put(
        f"/api/testruns/{run_id}/results/{case_id}",
        json={"status": status, "comment": comment},
        headers=headers,
    )


def test_requires_auth(client: TestClient) -> None:
    assert client.get("/api/testruns").status_code == 401


def test_create_planned_with_scope(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_case: Factory,
    make_run: Factory,
) -> None:
    p = make_project(auth_a)
    make_case(auth_a, p["id"], title="c1")
    make_case(auth_a, p["id"], title="c2", status="Ready")
    make_case(auth_a, p["id"], title="dep", status="Deprecated")
    run = make_run(auth_a, p["id"], name="Sprint 1", assignee="QA")
    assert run["status"] == "Planned"
    assert run["total_cases"] == 2  # Deprecated excluded
    assert run["executed"] == 0 and run["passed"] == 0
    assert run["assignee"] == "QA"
    assert {c["title"] for c in run["cases"]} == {"c1", "c2"}
    assert all(c["result"] is None for c in run["cases"])
    assert set(run["cases"][0]) == {
        "id",
        "title",
        "priority",
        "steps",
        "expected_result",
        "result",
    }


def test_status_lifecycle_and_reset(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_case: Factory,
    make_run: Factory,
) -> None:
    p = make_project(auth_a)
    c1 = make_case(auth_a, p["id"], title="c1")
    c2 = make_case(auth_a, p["id"], title="c2")
    run = make_run(auth_a, p["id"])
    rid = run["id"]

    r1 = _result(client, auth_a, rid, c1["id"], "Passed", "ok").json()
    assert r1["status"] == "In Progress"
    assert r1["executed"] == 1 and r1["passed"] == 1
    res = next(c for c in r1["cases"] if c["id"] == c1["id"])["result"]
    assert res["status"] == "Passed" and res["comment"] == "ok" and res["executed_at"]

    # upsert changes the same result, no double counting
    r1b = _result(client, auth_a, rid, c1["id"], "Failed", "regressed").json()
    assert r1b["executed"] == 1 and r1b["passed"] == 0
    assert r1b["status"] == "In Progress"

    r2 = _result(client, auth_a, rid, c2["id"], "Blocked").json()
    assert r2["status"] == "Completed"
    assert r2["executed"] == 2

    assert client.get(f"/api/testruns/{rid}", headers=auth_a).json()["status"] == "Completed"
    listed = client.get("/api/testruns?status=Completed", headers=auth_a).json()
    assert [x["id"] for x in listed] == [rid]
    assert "cases" not in listed[0]

    assert client.delete(f"/api/testruns/{rid}/results", headers=auth_a).status_code == 204
    after = client.get(f"/api/testruns/{rid}", headers=auth_a).json()
    assert after["status"] == "Planned"
    assert after["executed"] == 0
    assert all(c["result"] is None for c in after["cases"])
    assert client.get("/api/testruns?status=Planned", headers=auth_a).json()[0]["id"] == rid


def test_deprecated_cases_excluded_from_progress(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_case: Factory,
    make_run: Factory,
) -> None:
    p = make_project(auth_a)
    c1 = make_case(auth_a, p["id"], title="c1")
    c2 = make_case(auth_a, p["id"], title="c2")
    run = make_run(auth_a, p["id"])
    _result(client, auth_a, run["id"], c1["id"])
    # Deprecating the unexecuted case completes the run
    client.put(
        f"/api/testcases/{c2['id']}",
        json={"title": "c2", "status": "Deprecated"},
        headers=auth_a,
    )
    got = client.get(f"/api/testruns/{run['id']}", headers=auth_a).json()
    assert got["total_cases"] == 1
    assert got["status"] == "Completed"
    assert [c["id"] for c in got["cases"]] == [c1["id"]]
    # Deprecated case cannot receive results
    assert _result(client, auth_a, run["id"], c2["id"]).status_code == 404


def test_result_for_case_outside_scope_rejected(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
    make_case: Factory,
    make_run: Factory,
) -> None:
    p1, p2 = make_project(auth_a), make_project(auth_a)
    pb = make_project(auth_b)
    run = make_run(auth_a, p1["id"])
    other_project_case = make_case(auth_a, p2["id"])
    other_user_case = make_case(auth_b, pb["id"])
    assert _result(client, auth_a, run["id"], other_project_case["id"]).status_code == 404
    assert _result(client, auth_a, run["id"], other_user_case["id"]).status_code == 404
    assert _result(client, auth_a, run["id"], 99999).status_code == 404
    bad = client.put(
        f"/api/testruns/{run['id']}/results/1", json={"status": "Nope"}, headers=auth_a
    )
    assert bad.status_code == 422


def test_run_for_other_users_project_rejected(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
    make_run: Factory,
) -> None:
    pb = make_project(auth_b)
    r = client.post("/api/testruns", json={"project_id": pb["id"], "name": "x"}, headers=auth_a)
    assert r.status_code == 404
    pa = make_project(auth_a)
    run = make_run(auth_a, pa["id"])
    r = client.put(
        f"/api/testruns/{run['id']}", json={"name": "x", "project_id": pb["id"]}, headers=auth_a
    )
    assert r.status_code == 404


def test_update_and_move_project_clears_results(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_case: Factory,
    make_run: Factory,
) -> None:
    p1, p2 = make_project(auth_a), make_project(auth_a)
    c = make_case(auth_a, p1["id"])
    make_case(auth_a, p2["id"])
    make_case(auth_a, p2["id"])
    run = make_run(auth_a, p1["id"])
    _result(client, auth_a, run["id"], c["id"])

    r = client.put(f"/api/testruns/{run['id']}", json={"name": "Renamed"}, headers=auth_a)
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed" and r.json()["executed"] == 1

    r = client.put(
        f"/api/testruns/{run['id']}",
        json={"name": "Moved", "assignee": "bob", "project_id": p2["id"]},
        headers=auth_a,
    )
    body = r.json()
    assert body["project_id"] == p2["id"]
    assert body["executed"] == 0 and body["status"] == "Planned"
    assert body["total_cases"] == 2
    assert body["assignee"] == "bob"


def test_filters_validation_delete(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_run: Factory,
) -> None:
    p1, p2 = make_project(auth_a), make_project(auth_a)
    make_run(auth_a, p1["id"], name="Smoke Run", assignee="dana")
    r2 = make_run(auth_a, p2["id"], name="Regression")

    def names(qs: str) -> list[str]:
        return [x["name"] for x in client.get(f"/api/testruns?{qs}", headers=auth_a).json()]

    assert names("") == ["Regression", "Smoke Run"]
    assert names(f"project_id={p1['id']}") == ["Smoke Run"]
    assert names("q=DANA") == ["Smoke Run"]
    assert names("q=regress") == ["Regression"]
    assert names("limit=1") == ["Regression"]
    assert client.get("/api/testruns?status=Bogus", headers=auth_a).status_code == 422
    assert (
        client.post(
            "/api/testruns", json={"project_id": p1["id"], "name": "  "}, headers=auth_a
        ).status_code
        == 422
    )
    assert client.delete(f"/api/testruns/{r2['id']}", headers=auth_a).status_code == 204
    assert client.get(f"/api/testruns/{r2['id']}", headers=auth_a).status_code == 404


def test_cross_user_isolation(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
    make_case: Factory,
    make_run: Factory,
) -> None:
    p = make_project(auth_a)
    case = make_case(auth_a, p["id"])
    run = make_run(auth_a, p["id"])
    rid = run["id"]
    assert client.get("/api/testruns", headers=auth_b).json() == []
    assert client.get(f"/api/testruns?project_id={p['id']}", headers=auth_b).json() == []
    assert client.get(f"/api/testruns/{rid}", headers=auth_b).status_code == 404
    assert client.put(f"/api/testruns/{rid}", json={"name": "h"}, headers=auth_b).status_code == 404
    assert client.delete(f"/api/testruns/{rid}", headers=auth_b).status_code == 404
    assert _result(client, auth_b, rid, case["id"]).status_code == 404
    assert client.delete(f"/api/testruns/{rid}/results", headers=auth_b).status_code == 404
    still = client.get(f"/api/testruns/{rid}", headers=auth_a).json()
    assert still["executed"] == 0
