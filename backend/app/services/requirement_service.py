"""Requirement business logic (all queries scoped to the owning user)."""

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import Project, Requirement, RequirementPriority, RequirementStatus, TestCase
from app.schemas.requirement import (
    LinkedTestCase,
    RequirementCreate,
    RequirementDetail,
    RequirementRead,
    RequirementUpdate,
)
from app.services.common import LIKE_ESCAPE, like_pattern

DETAIL_TEST_CASE_LIMIT = 1000


def _to_read(req: Requirement, count: int) -> RequirementRead:
    data = RequirementRead.model_validate(req)
    data.test_case_count = count
    return data


def _get_owned(db: Session, user_id: int, requirement_id: int) -> Requirement:
    req = db.scalar(
        select(Requirement).where(Requirement.id == requirement_id, Requirement.user_id == user_id)
    )
    if req is None:
        raise NotFoundError("Requirement")
    return req


def _count_for(db: Session, requirement_id: int) -> int:
    return (
        db.scalar(select(func.count(TestCase.id)).where(TestCase.requirement_id == requirement_id))
        or 0
    )


def list_requirements(
    db: Session,
    user_id: int,
    *,
    project_id: int | None,
    priority: RequirementPriority | None,
    status: RequirementStatus | None,
    q: str | None,
    limit: int,
    offset: int,
) -> list[RequirementRead]:
    counts = (
        select(TestCase.requirement_id.label("rid"), func.count(TestCase.id).label("cnt"))
        .where(TestCase.requirement_id.is_not(None), TestCase.user_id == user_id)
        .group_by(TestCase.requirement_id)
        .subquery()
    )
    stmt = (
        select(Requirement, func.coalesce(counts.c.cnt, 0))
        .outerjoin(counts, counts.c.rid == Requirement.id)
        .where(Requirement.user_id == user_id)
    )
    if project_id is not None:
        stmt = stmt.where(Requirement.project_id == project_id)
    if priority is not None:
        stmt = stmt.where(Requirement.priority == priority.value)
    if status is not None:
        stmt = stmt.where(Requirement.status == status.value)
    if q and q.strip():
        like = like_pattern(q).lower()
        stmt = stmt.where(
            func.lower(Requirement.title).like(like, escape=LIKE_ESCAPE)
            | func.lower(func.coalesce(Requirement.description, "")).like(like, escape=LIKE_ESCAPE)
        )
    stmt = stmt.order_by(Requirement.id.desc()).limit(limit).offset(offset)
    return [_to_read(req, int(cnt)) for req, cnt in db.execute(stmt).all()]


def get_requirement(db: Session, user_id: int, requirement_id: int) -> RequirementDetail:
    req = _get_owned(db, user_id, requirement_id)
    cases = db.scalars(
        select(TestCase)
        .where(TestCase.requirement_id == req.id, TestCase.user_id == user_id)
        .order_by(TestCase.id)
        .limit(DETAIL_TEST_CASE_LIMIT)
    ).all()
    base = RequirementRead.model_validate(req)
    return RequirementDetail(
        **base.model_dump(exclude={"test_case_count"}),
        test_case_count=_count_for(db, req.id),
        test_cases=[LinkedTestCase.model_validate(c) for c in cases],
    )


def create_requirement(db: Session, user_id: int, body: RequirementCreate) -> RequirementRead:
    project = db.scalar(
        select(Project).where(Project.id == body.project_id, Project.user_id == user_id)
    )
    if project is None:
        raise NotFoundError("Project")
    req = Requirement(
        user_id=user_id,
        project_id=project.id,
        title=body.title,
        description=body.description,
        priority=body.priority.value,
        status=body.status.value,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _to_read(req, 0)


def update_requirement(
    db: Session, user_id: int, requirement_id: int, body: RequirementUpdate
) -> RequirementRead:
    req = _get_owned(db, user_id, requirement_id)
    req.title = body.title
    req.description = body.description
    req.priority = body.priority.value
    req.status = body.status.value
    db.commit()
    db.refresh(req)
    return _to_read(req, _count_for(db, req.id))


def delete_requirement(db: Session, user_id: int, requirement_id: int) -> None:
    req = _get_owned(db, user_id, requirement_id)
    # Detach linked test cases explicitly so behaviour does not depend on the
    # database enforcing ON DELETE SET NULL (SQLite has foreign keys off by default).
    db.execute(
        update(TestCase).where(TestCase.requirement_id == req.id).values(requirement_id=None)
    )
    db.delete(req)
    db.commit()
