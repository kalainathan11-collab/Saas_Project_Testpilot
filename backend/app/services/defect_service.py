"""Business logic for defects (all queries scoped by user_id)."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import Defect, Project, TestCase
from app.schemas.defect import DefectCreate, DefectUpdate
from app.services.common import LIKE_ESCAPE, like_pattern


def _validate_refs(db: Session, user_id: int, project_id: int, test_case_id: int | None) -> None:
    project = db.scalar(
        select(Project.id).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        raise NotFoundError("Project")
    if test_case_id is not None:
        found = db.scalar(
            select(TestCase.id).where(
                TestCase.id == test_case_id,
                TestCase.user_id == user_id,
                TestCase.project_id == project_id,
            )
        )
        if found is None:
            raise NotFoundError("Test case")


def list_defects(
    db: Session,
    user_id: int,
    *,
    project_id: int | None = None,
    severity: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[Defect]:
    stmt = select(Defect).where(Defect.user_id == user_id)
    if project_id is not None:
        stmt = stmt.where(Defect.project_id == project_id)
    if severity:
        stmt = stmt.where(Defect.severity == severity)
    if status:
        stmt = stmt.where(Defect.status == status)
    if q and q.strip():
        like = like_pattern(q)
        stmt = stmt.where(
            or_(
                Defect.title.ilike(like, escape=LIKE_ESCAPE),
                Defect.description.ilike(like, escape=LIKE_ESCAPE),
            )
        )
    stmt = stmt.order_by(Defect.id.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


def get_defect(db: Session, user_id: int, defect_id: int) -> Defect:
    defect = db.scalar(select(Defect).where(Defect.id == defect_id, Defect.user_id == user_id))
    if defect is None:
        raise NotFoundError("Defect")
    return defect


def create_defect(db: Session, user_id: int, data: DefectCreate) -> Defect:
    _validate_refs(db, user_id, data.project_id, data.test_case_id)
    defect = Defect(
        user_id=user_id,
        project_id=data.project_id,
        test_case_id=data.test_case_id,
        title=data.title,
        description=data.description,
        severity=data.severity.value,
        status=data.status.value,
        assignee=data.assignee,
    )
    db.add(defect)
    db.commit()
    db.refresh(defect)
    return defect


def update_defect(db: Session, user_id: int, defect_id: int, data: DefectUpdate) -> Defect:
    defect = get_defect(db, user_id, defect_id)
    _validate_refs(db, user_id, data.project_id, data.test_case_id)
    defect.project_id = data.project_id
    defect.test_case_id = data.test_case_id
    defect.title = data.title
    defect.description = data.description
    defect.severity = data.severity.value
    defect.status = data.status.value
    defect.assignee = data.assignee
    db.commit()
    db.refresh(defect)
    return defect


def delete_defect(db: Session, user_id: int, defect_id: int) -> None:
    defect = get_defect(db, user_id, defect_id)
    db.delete(defect)
    db.commit()
