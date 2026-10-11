"""Test runs endpoints (/api/testruns)."""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.dependencies import CurrentUser, DbSession
from app.models import TestRunStatus
from app.schemas.test_run import (
    TestRunCreate,
    TestRunDetailOut,
    TestRunOut,
    TestRunResultIn,
    TestRunUpdate,
)
from app.services.test_run_service import TestRunService

router = APIRouter(prefix="/api/testruns", tags=["testruns"])


@router.get("", response_model=list[TestRunOut])
def list_test_runs(
    user: CurrentUser,
    db: DbSession,
    project_id: int | None = None,
    status_: Annotated[TestRunStatus | None, Query(alias="status")] = None,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TestRunOut]:
    return TestRunService(db, user.id).list(project_id, status_, q, limit, offset)


@router.post("", response_model=TestRunDetailOut, status_code=status.HTTP_201_CREATED)
def create_test_run(data: TestRunCreate, user: CurrentUser, db: DbSession) -> TestRunDetailOut:
    return TestRunService(db, user.id).create(data)


@router.get("/{run_id}", response_model=TestRunDetailOut)
def get_test_run(run_id: int, user: CurrentUser, db: DbSession) -> TestRunDetailOut:
    return TestRunService(db, user.id).detail(run_id)


@router.put("/{run_id}", response_model=TestRunDetailOut)
def update_test_run(
    run_id: int, data: TestRunUpdate, user: CurrentUser, db: DbSession
) -> TestRunDetailOut:
    return TestRunService(db, user.id).update(run_id, data)


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_run(run_id: int, user: CurrentUser, db: DbSession) -> Response:
    TestRunService(db, user.id).delete(run_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{run_id}/results/{case_id}", response_model=TestRunDetailOut)
def upsert_result(
    run_id: int, case_id: int, data: TestRunResultIn, user: CurrentUser, db: DbSession
) -> TestRunDetailOut:
    return TestRunService(db, user.id).upsert_result(run_id, case_id, data)


@router.delete("/{run_id}/results", status_code=status.HTTP_204_NO_CONTENT)
def clear_results(run_id: int, user: CurrentUser, db: DbSession) -> Response:
    TestRunService(db, user.id).clear_results(run_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
