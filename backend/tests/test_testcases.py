"""Test cases module tests (including CSV export)."""

import csv
import io

from fastapi.testclient import TestClient

from tests.conftest import Factory


def _rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def test_requires_auth(client: TestClient) -> None:
    assert client.get("/api/testcases").status_code == 401
    assert client.get("/api/testcases/export").status_code == 401


def test_crud(client: TestClient, auth_a: dict[str, str], make_project: Factory) -> None:
    p = make_project(auth_a)
    body = {
        "project_id": p["id"],
        "title": "  Login with valid creds ",
        "module": "Auth",
        "type": "Smoke",
        "priority": "High",
        "status": "Ready",
        "preconditions": "user exists",
        "steps": "1. open\n2. submit",
        "expected_result": "logged in",
    }
    r = client.post("/api/testcases", json=body, headers=auth_a)
    assert r.status_code == 201
    tc = r.json()
    assert tc["title"] == "Login with valid creds"
    assert tc["steps"] == "1. open\n2. submit"
    assert tc["requirement_id"] is None

    assert client.get(f"/api/testcases/{tc['id']}", headers=auth_a).json()["module"] == "Auth"

    upd = client.put(
        f"/api/testcases/{tc['id']}",
        json={"title": "Renamed", "type": "API", "priority": "Low", "status": "Draft"},
        headers=auth_a,
    )
    assert upd.status_code == 200
    out = upd.json()
    assert out["title"] == "Renamed" and out["type"] == "API"
    assert out["project_id"] == p["id"]  # project_id omitted -> kept
    assert out["module"] is None  # full-replace semantics

    assert client.delete(f"/api/testcases/{tc['id']}", headers=auth_a).status_code == 204
    assert client.get(f"/api/testcases/{tc['id']}", headers=auth_a).status_code == 404


def test_defaults_and_validation(
    client: TestClient, auth_a: dict[str, str], make_project: Factory
) -> None:
    p = make_project(auth_a)
    tc = client.post(
        "/api/testcases", json={"project_id": p["id"], "title": "t"}, headers=auth_a
    ).json()
    assert (tc["type"], tc["priority"], tc["status"]) == ("Functional", "Medium", "Draft")
    for bad in (
        {"project_id": p["id"], "title": " "},
        {"project_id": p["id"], "title": "t", "type": "Nope"},
        {"project_id": p["id"], "title": "t", "priority": "Nope"},
        {"title": "no project"},
    ):
        assert client.post("/api/testcases", json=bad, headers=auth_a).status_code == 422


def test_filters(
    client: TestClient,
    auth_a: dict[str, str],
    make_project: Factory,
    make_requirement: Factory,
    make_case: Factory,
) -> None:
    p1, p2 = make_project(auth_a), make_project(auth_a)
    req = make_requirement(auth_a, p1["id"])
    make_case(
        auth_a, p1["id"], title="Alpha", type="API", priority="High", requirement_id=req["id"]
    )
    make_case(auth_a, p1["id"], title="Beta", module="Pay_ment", status="Ready")
    make_case(auth_a, p2["id"], title="Gamma 100%")

    def titles(qs: str) -> list[str]:
        return [x["title"] for x in client.get(f"/api/testcases?{qs}", headers=auth_a).json()]

    assert titles("") == ["Gamma 100%", "Beta", "Alpha"]
    assert titles(f"project_id={p1['id']}") == ["Beta", "Alpha"]
    assert titles(f"requirement_id={req['id']}") == ["Alpha"]
    assert titles("type=API") == ["Alpha"]
    assert titles("priority=High") == ["Alpha"]
    assert titles("status=Ready") == ["Beta"]
    assert titles("q=ALPH") == ["Alpha"]
    assert titles("q=pay_") == ["Beta"]  # module search; underscore treated literally
    assert titles("q=%25") == ["Gamma 100%"]  # '%' is literal, not a wildcard
    assert titles("limit=1&offset=1") == ["Beta"]


def test_requirement_must_be_owned_and_same_project(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
    make_requirement: Factory,
    make_case: Factory,
) -> None:
    pa1, pa2 = make_project(auth_a), make_project(auth_a)
    pb = make_project(auth_b)
    req_b = make_requirement(auth_b, pb["id"])
    req_a2 = make_requirement(auth_a, pa2["id"])

    # other user's project
    r = client.post("/api/testcases", json={"project_id": pb["id"], "title": "x"}, headers=auth_a)
    assert r.status_code == 404
    # other user's requirement
    r = client.post(
        "/api/testcases",
        json={"project_id": pa1["id"], "title": "x", "requirement_id": req_b["id"]},
        headers=auth_a,
    )
    assert r.status_code == 404
    # own requirement but from a different project
    r = client.post(
        "/api/testcases",
        json={"project_id": pa1["id"], "title": "x", "requirement_id": req_a2["id"]},
        headers=auth_a,
    )
    assert r.status_code == 422

    case = make_case(auth_a, pa1["id"])
    # update: other user's requirement / project
    r = client.put(
        f"/api/testcases/{case['id']}",
        json={"title": "x", "requirement_id": req_b["id"]},
        headers=auth_a,
    )
    assert r.status_code == 404
    r = client.put(
        f"/api/testcases/{case['id']}",
        json={"title": "x", "project_id": pb["id"]},
        headers=auth_a,
    )
    assert r.status_code == 404
    # moving to own other project works; requirement must match new project
    r = client.put(
        f"/api/testcases/{case['id']}",
        json={"title": "x", "project_id": pa2["id"], "requirement_id": req_a2["id"]},
        headers=auth_a,
    )
    assert r.status_code == 200
    assert r.json()["project_id"] == pa2["id"]


def test_export_csv(
    client: TestClient, auth_a: dict[str, str], make_project: Factory, make_case: Factory
) -> None:
    p = make_project(auth_a)
    make_case(auth_a, p["id"], title="Normal", steps="a,b\nc", type="API")
    make_case(auth_a, p["id"], title="Other")
    r = client.get("/api/testcases/export", headers=auth_a)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    rows = _rows(r.text)
    assert len(rows) == 2
    assert list(rows[0])[:6] == ["id", "project_id", "requirement_id", "title", "module", "type"]
    normal = next(x for x in rows if x["title"] == "Normal")
    assert normal["steps"] == "a,b\nc"  # quoted correctly, round-trips

    filtered = _rows(client.get("/api/testcases/export?type=API", headers=auth_a).text)
    assert [x["title"] for x in filtered] == ["Normal"]


def test_export_neutralises_formula_injection(
    client: TestClient, auth_a: dict[str, str], make_project: Factory, make_case: Factory
) -> None:
    p = make_project(auth_a)
    evil = ["=1+1", "+SUM(A1)", "-2+3", "@cmd", '=HYPERLINK("http://x")']
    for i, v in enumerate(evil):
        make_case(auth_a, p["id"], title=v, module=v, steps=v, expected_result=f"{v}{i}")
    rows = _rows(client.get("/api/testcases/export", headers=auth_a).text)
    assert len(rows) == len(evil)
    for row in rows:
        for col in ("title", "module", "steps", "expected_result"):
            assert row[col].startswith("'"), (col, row[col])
            assert row[col][1] in "=+-@"


def test_export_is_user_scoped(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
    make_case: Factory,
) -> None:
    p = make_project(auth_a)
    make_case(auth_a, p["id"])
    assert _rows(client.get("/api/testcases/export", headers=auth_b).text) == []
    assert (
        _rows(client.get(f"/api/testcases/export?project_id={p['id']}", headers=auth_b).text) == []
    )
    assert len(_rows(client.get("/api/testcases/export", headers=auth_a).text)) == 1


def test_cross_user_isolation(
    client: TestClient,
    auth_a: dict[str, str],
    auth_b: dict[str, str],
    make_project: Factory,
    make_case: Factory,
) -> None:
    p = make_project(auth_a)
    case = make_case(auth_a, p["id"])
    cid = case["id"]
    assert client.get("/api/testcases", headers=auth_b).json() == []
    assert client.get(f"/api/testcases?project_id={p['id']}", headers=auth_b).json() == []
    assert client.get(f"/api/testcases/{cid}", headers=auth_b).status_code == 404
    r = client.put(f"/api/testcases/{cid}", json={"title": "hack"}, headers=auth_b)
    assert r.status_code == 404
    assert client.delete(f"/api/testcases/{cid}", headers=auth_b).status_code == 404
    assert client.get(f"/api/testcases/{cid}", headers=auth_a).json()["title"] == case["title"]
