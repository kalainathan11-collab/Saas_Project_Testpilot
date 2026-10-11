"""Business logic for test cases."""

import csv
import io

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.exceptions import AppError, NotFoundError
from app.models import Project, Requirement, TestCase
from app.schemas.test_case import TestCaseCreate, TestCaseUpdate
from app.services.common import LIKE_ESCAPE, like_pattern

EXPORT_MAX_ROWS = 10000

CSV_COLUMNS = [
    "id",
    "project_id",
    "requirement_id",
    "title",
    "module",
    "type",
    "priority",
    "status",
    "preconditions",
    "steps",
    "expected_result",
    "created_at",
    "updated_at",
]
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


class ValidationFailedError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


def _ensure_project(db: Session, user_id: int, project_id: int) -> None:
    found = db.scalar(
        select(Project.id).where(Project.id == project_id, Project.user_id == user_id)
    )
    if found is None:
        raise NotFoundError("Project")


def _ensure_requirement(db: Session, user_id: int, requirement_id: int, project_id: int) -> None:
    req = db.scalar(
        select(Requirement).where(Requirement.id == requirement_id, Requirement.user_id == user_id)
    )
    if req is None:
        raise NotFoundError("Requirement")
    if req.project_id != project_id:
        raise ValidationFailedError("Requirement does not belong to the test case's project")


def list_test_cases(
    db: Session,
    user_id: int,
    *,
    project_id: int | None = None,
    requirement_id: int | None = None,
    type_: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int | None = 200,
    offset: int = 0,
) -> list[TestCase]:
    stmt = select(TestCase).where(TestCase.user_id == user_id)
    if project_id is not None:
        stmt = stmt.where(TestCase.project_id == project_id)
    if requirement_id is not None:
        stmt = stmt.where(TestCase.requirement_id == requirement_id)
    if type_:
        stmt = stmt.where(TestCase.type == type_)
    if priority:
        stmt = stmt.where(TestCase.priority == priority)
    if status:
        stmt = stmt.where(TestCase.status == status)
    if q and q.strip():
        pattern = like_pattern(q)
        stmt = stmt.where(
            or_(
                TestCase.title.ilike(pattern, escape=LIKE_ESCAPE),
                TestCase.module.ilike(pattern, escape=LIKE_ESCAPE),
            )
        )
    stmt = stmt.order_by(TestCase.id.desc()).offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())


def get_test_case(db: Session, user_id: int, case_id: int) -> TestCase:
    case = db.scalar(select(TestCase).where(TestCase.id == case_id, TestCase.user_id == user_id))
    if case is None:
        raise NotFoundError("Test case")
    return case


def create_test_case(db: Session, user_id: int, data: TestCaseCreate) -> TestCase:
    _ensure_project(db, user_id, data.project_id)
    if data.requirement_id is not None:
        _ensure_requirement(db, user_id, data.requirement_id, data.project_id)
    values = data.model_dump()
    for key in ("type", "priority", "status"):
        values[key] = values[key].value
    case = TestCase(user_id=user_id, **values)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def update_test_case(db: Session, user_id: int, case_id: int, data: TestCaseUpdate) -> TestCase:
    case = get_test_case(db, user_id, case_id)
    project_id = data.project_id if data.project_id is not None else case.project_id
    if project_id != case.project_id:
        _ensure_project(db, user_id, project_id)
    if data.requirement_id is not None:
        _ensure_requirement(db, user_id, data.requirement_id, project_id)
    values = data.model_dump(exclude={"project_id"})
    for key in ("type", "priority", "status"):
        values[key] = values[key].value
    for key, value in values.items():
        setattr(case, key, value)
    case.project_id = project_id
    db.commit()
    db.refresh(case)
    return case


def delete_test_case(db: Session, user_id: int, case_id: int) -> None:
    case = get_test_case(db, user_id, case_id)
    db.delete(case)
    db.commit()


def _safe_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if text.startswith(_FORMULA_PREFIXES):
        return "'" + text
    return text


def export_csv(cases: list[TestCase]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow(CSV_COLUMNS)
    for case in cases:
        writer.writerow([_safe_cell(getattr(case, col)) for col in CSV_COLUMNS])
    return buf.getvalue()
