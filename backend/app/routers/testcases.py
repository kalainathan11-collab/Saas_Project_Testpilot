"""Test case endpoints (/api/testcases)."""

from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.dependencies import CurrentUser, DbSession
from app.schemas.test_case import TestCaseCreate, TestCaseOut, TestCaseUpdate
from app.services import test_case_service as service

router = APIRouter(prefix="/api/testcases", tags=["testcases"])


@router.get("/export")
def export_test_cases(
    db: DbSession,
    user: CurrentUser,
    project_id: int | None = None,
    requirement_id: int | None = None,
    type: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    q: str | None = None,
) -> Response:
    cases = service.list_test_cases(
        db,
        user.id,
        project_id=project_id,
        requirement_id=requirement_id,
        type_=type,
        priority=priority,
        status=status,
        q=q,
        limit=None,
    )
    return Response(
        content=service.export_csv(cases),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="test-cases.csv"'},
    )


@router.get("", response_model=list[TestCaseOut])
def list_test_cases(
    db: DbSession,
    user: CurrentUser,
    project_id: int | None = None,
    requirement_id: int | None = None,
    type: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TestCaseOut]:
    cases = service.list_test_cases(
        db,
        user.id,
        project_id=project_id,
        requirement_id=requirement_id,
        type_=type,
        priority=priority,
        status=status,
        q=q,
        limit=limit,
        offset=offset,
    )
    return [TestCaseOut.model_validate(c) for c in cases]


@router.post("", response_model=TestCaseOut, status_code=201)
def create_test_case(body: TestCaseCreate, db: DbSession, user: CurrentUser) -> TestCaseOut:
    return TestCaseOut.model_validate(service.create_test_case(db, user.id, body))


@router.get("/{case_id}", response_model=TestCaseOut)
def get_test_case(case_id: int, db: DbSession, user: CurrentUser) -> TestCaseOut:
    return TestCaseOut.model_validate(service.get_test_case(db, user.id, case_id))


@router.put("/{case_id}", response_model=TestCaseOut)
def update_test_case(
    case_id: int, body: TestCaseUpdate, db: DbSession, user: CurrentUser
) -> TestCaseOut:
    return TestCaseOut.model_validate(service.update_test_case(db, user.id, case_id, body))


@router.delete("/{case_id}", status_code=204)
def delete_test_case(case_id: int, db: DbSession, user: CurrentUser) -> Response:
    service.delete_test_case(db, user.id, case_id)
    return Response(status_code=204)
