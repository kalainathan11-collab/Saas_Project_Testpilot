"""Project business logic. Every query is scoped to the owning user."""

from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.exceptions import ConflictError, NotFoundError
from app.models import (
    Defect,
    Project,
    Requirement,
    TestCase,
    TestResult,
    TestRun,
    User,
)
from app.schemas.project import (
    ProjectCounts,
    ProjectCreate,
    ProjectDetail,
    ProjectOut,
    ProjectUpdate,
)
from app.services.common import LIKE_ESCAPE, like_pattern


def to_out(project: Project, user: User) -> ProjectOut:
    out = ProjectOut.model_validate(project)
    out.owner = user.full_name or user.email
    return out


def _get_owned(db: Session, user: User, project_id: int) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    if project is None:
        raise NotFoundError("Project")
    return project


def _key_taken(db: Session, user: User, key: str, exclude_id: int | None = None) -> bool:
    stmt = select(Project.id).where(Project.user_id == user.id, Project.key == key)
    if exclude_id is not None:
        stmt = stmt.where(Project.id != exclude_id)
    return db.scalar(stmt) is not None


def list_projects(
    db: Session,
    user: User,
    q: str | None,
    status: str | None,
    limit: int,
    offset: int,
) -> list[ProjectOut]:
    stmt = select(Project).where(Project.user_id == user.id)
    if q and q.strip():
        like = like_pattern(q)
        stmt = stmt.where(
            or_(
                Project.name.ilike(like, escape=LIKE_ESCAPE),
                Project.key.ilike(like, escape=LIKE_ESCAPE),
                Project.description.ilike(like, escape=LIKE_ESCAPE),
            )
        )
    if status:
        stmt = stmt.where(Project.status == status)
    stmt = stmt.order_by(Project.id.desc()).limit(limit).offset(offset)
    return [to_out(p, user) for p in db.scalars(stmt)]


def _count(db: Session, id_col: InstrumentedAttribute[int], project_id: int, user_id: int) -> int:
    owner_col = id_col.class_.user_id
    project_col = id_col.class_.project_id
    stmt = select(func.count(id_col)).where(project_col == project_id, owner_col == user_id)
    return int(db.scalar(stmt) or 0)


def get_project(db: Session, user: User, project_id: int) -> ProjectDetail:
    project = _get_owned(db, user, project_id)
    counts = ProjectCounts(
        requirements=_count(db, Requirement.id, project.id, user.id),
        test_cases=_count(db, TestCase.id, project.id, user.id),
        test_runs=_count(db, TestRun.id, project.id, user.id),
        defects=_count(db, Defect.id, project.id, user.id),
    )
    base = to_out(project, user)
    return ProjectDetail(**base.model_dump(), counts=counts)


def create_project(db: Session, user: User, data: ProjectCreate) -> ProjectOut:
    if _key_taken(db, user, data.key):
        raise ConflictError(f"Project key '{data.key}' already exists")
    project = Project(
        user_id=user.id,
        name=data.name,
        key=data.key,
        description=data.description,
        status=data.status.value,
    )
    db.add(project)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"Project key '{data.key}' already exists") from exc
    db.refresh(project)
    return to_out(project, user)


def update_project(db: Session, user: User, project_id: int, data: ProjectUpdate) -> ProjectOut:
    project = _get_owned(db, user, project_id)
    if _key_taken(db, user, data.key, exclude_id=project.id):
        raise ConflictError(f"Project key '{data.key}' already exists")
    project.name = data.name
    project.key = data.key
    project.description = data.description
    project.status = data.status.value
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"Project key '{data.key}' already exists") from exc
    db.refresh(project)
    return to_out(project, user)


def delete_project(db: Session, user: User, project_id: int) -> None:
    """Delete a project and all children explicitly (works without FK enforcement)."""
    project = _get_owned(db, user, project_id)
    run_ids = select(TestRun.id).where(TestRun.project_id == project.id)
    case_ids = select(TestCase.id).where(TestCase.project_id == project.id)
    db.execute(
        delete(TestResult).where(
            or_(TestResult.test_run_id.in_(run_ids), TestResult.test_case_id.in_(case_ids))
        )
    )
    db.execute(delete(Defect).where(Defect.project_id == project.id))
    db.execute(delete(TestCase).where(TestCase.project_id == project.id))
    db.execute(delete(TestRun).where(TestRun.project_id == project.id))
    db.execute(delete(Requirement).where(Requirement.project_id == project.id))
    db.execute(delete(Project).where(Project.id == project.id))
    db.commit()
