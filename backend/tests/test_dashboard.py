"""Dashboard summary and reports tests."""

import csv
import io
from typing import Any

from fastapi.testclient import TestClient

from app.services.dashboard_service import csv_safe, pct
from tests.conftest import Factory


def _seed(
    client: TestClient,
    h: dict[str, str],
    make_project: Factory,
    make_requirement: Factory,
    make_case: Factory,
    make_run: Factory,
    make_defect: Factory,
) -> dict[str, Any]:
    p = make_project(h, name="Shop", key="SHOP")
    req1 = make_requirement(h, p["id"], title="r1")
    make_requirement(h, p["id"], title="r2")
    c1 = make_case(h, p["id"], title="c1", requirement_id=req1["id"])
    c2 = make_case(h, p["id"], title="c2")
    c3 = make_case(h, p["id"], title="c3")
    make_case(h, p["id"], title="old", status="Deprecated")
    run = make_run(h, p["id"], name="Run A")
    for case, status in ((c1, "Passed"), (c2, "Passed"), (c3, "Failed")):
        r = client.put(
            f"/api/testruns/{run['id']}/results/{case['id']}",
            json={"status": status},
            headers=h,
        )
        assert r.status_code == 200
    make_defect(h, p["id"], title="d1", severity="Blocker")
    make_defect(h, p["id"], title="d2", severity="Minor", status="In Progress")
    make_defect(h, p["id"], title="d3", severity="Minor", status="Closed")
    return p


def test_requires_auth(client: TestClient) -> None:
    assert client.get("/api/dashboard/summary").status_code == 401
    assert client.get("/api/reports/projects").status_code == 401


def test_zero_safe_for_new_user(client: TestClient, auth_a: dict[str, str]) -> None:
    r = client.get("/api/dashboard/summary", headers=auth_a)
    assert r.status_code == 200
    assert r.json() == {
        "test_cases": 0,
        "test_runs": 0,
        "executed": 0,
        "pass_rate": 0,
        "open_defects": 0,
        "results": {"Passed": 0, "Failed": 0, "Blocked": 0, "Skipped": 0},
        "defects_by_severity": {"Minor": 0, "Major": 0, "Critical": 0, "Blocker": 0},
        "runs": [],
        "recent_defects": [],
    }
    assert client.get("/api/reports/projects", headers=auth_a).json() == []
    csv_text = client.get("/api/reports/projects?format=csv", headers=auth_a).text
    assert csv_text.strip().split("\r\n") == [
        "project_id,project,test_cases,requirements,coverage_pct,runs,executed,pass_rate,"
        "open_defects,defects"
    ]


def test_zero_safe_empty_project(
    client: TestClient, auth_a: dict[str, str], make_project: Factory
) -> None:
    p = make_project(auth_a)
    s = client.get(f"/api/dashboard/summary?project_id={p['id']}", headers=auth_a).json()
    assert s["pass_rate"] == 0 and s["test_cases"] == 0
    rep = client.get(f"/api/reports/projects?project_id={p['id']}", headers=auth_a).json()
    assert rep[0]["coverage_pct"] == 0 and rep[0]["pass_rate"] == 0


def test_summary_numbers(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_requirement: Factory,
    make_case: Factory,
    make_run: Factory,
    make_defect: Factory,
) -> None:
    p = _seed(client, auth_a, make_project, make_requirement, make_case, make_run, make_defect)
    s = client.get("/api/dashboard/summary", headers=auth_a).json()
    assert s["test_cases"] == 4
    assert s["test_runs"] == 1
    assert s["executed"] == 3
    assert s["pass_rate"] == 67
    assert s["results"] == {"Passed": 2, "Failed": 1, "Blocked": 0, "Skipped": 0}
    assert s["open_defects"] == 2  # Open + In Progress
    assert s["defects_by_severity"] == {"Minor": 2, "Major": 0, "Critical": 0, "Blocker": 1}
    assert s["runs"] == [{"id": s["runs"][0]["id"], "name": "Run A", "progress_pct": 100}]
    assert [d["title"] for d in s["recent_defects"]] == ["d3", "d2", "d1"]

    scoped = client.get(f"/api/dashboard/summary?project_id={p['id']}", headers=auth_a).json()
    assert scoped == s


def test_recent_defects_capped_at_five(
    client: TestClient, auth_a: dict[str, str], make_project: Factory, make_defect: Factory
) -> None:
    p = make_project(auth_a)
    for i in range(7):
        make_defect(auth_a, p["id"], title=f"d{i}")
    s = client.get("/api/dashboard/summary", headers=auth_a).json()
    assert len(s["recent_defects"]) == 5
    assert s["recent_defects"][0]["title"] == "d6"


def test_project_scoping(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_requirement: Factory,
    make_case: Factory,
    make_run: Factory,
    make_defect: Factory,
) -> None:
    _seed(client, auth_a, make_project, make_requirement, make_case, make_run, make_defect)
    other = make_project(auth_a, name="Empty", key="EMP")
    s = client.get(f"/api/dashboard/summary?project_id={other['id']}", headers=auth_a).json()
    assert s["test_cases"] == 0 and s["executed"] == 0 and s["open_defects"] == 0


def test_report_json_and_csv(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_requirement: Factory,
    make_case: Factory,
    make_run: Factory,
    make_defect: Factory,
) -> None:
    p = _seed(client, auth_a, make_project, make_requirement, make_case, make_run, make_defect)
    rows = client.get("/api/reports/projects", headers=auth_a).json()
    assert rows == [
        {
            "project_id": p["id"],
            "project": "Shop",
            "test_cases": 4,
            "requirements": 2,
            "coverage_pct": 50,
            "runs": 1,
            "executed": 3,
            "pass_rate": 67,
            "open_defects": 2,
            "defects": 3,
        }
    ]
    r = client.get("/api/reports/projects?format=csv", headers=auth_a)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    parsed = list(csv.DictReader(io.StringIO(r.text)))
    assert parsed[0]["project"] == "Shop" and parsed[0]["pass_rate"] == "67"
    assert client.get("/api/reports/projects?format=xml", headers=auth_a).status_code == 422


def test_csv_neutralises_formula_in_project_name(
    client: TestClient, auth_a: dict[str, str], make_project: Factory
) -> None:
    make_project(auth_a, name="=cmd|' /C calc'!A0", key="EVIL")
    r = client.get("/api/reports/projects?format=csv", headers=auth_a)
    parsed = list(csv.DictReader(io.StringIO(r.text)))
    assert parsed[0]["project"].startswith("'=")


def test_helpers() -> None:
    assert pct(1, 0) == 0
    assert pct(5, 3) == 100
    assert pct(1, 3) == 33
    assert csv_safe("=x") == "'=x"
    assert csv_safe("ok") == "ok"
    assert csv_safe("") == ""


def test_cross_user_isolation(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
    make_requirement: Factory,
    make_case: Factory,
    make_run: Factory,
    make_defect: Factory,
) -> None:
    p = _seed(client, auth_a, make_project, make_requirement, make_case, make_run, make_defect)
    s = client.get("/api/dashboard/summary", headers=auth_b).json()
    assert s["test_cases"] == 0 and s["test_runs"] == 0 and s["executed"] == 0
    assert s["open_defects"] == 0 and s["runs"] == [] and s["recent_defects"] == []
    assert client.get("/api/reports/projects", headers=auth_b).json() == []
    # other user's project_id -> 404
    assert (
        client.get(f"/api/dashboard/summary?project_id={p['id']}", headers=auth_b).status_code
        == 404
    )
    assert (
        client.get(f"/api/reports/projects?project_id={p['id']}", headers=auth_b).status_code == 404
    )
