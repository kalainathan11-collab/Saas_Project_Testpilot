"""Projects router: CRUD under /api/projects."""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.dependencies import CurrentUser, DbSession
from app.models import ProjectStatus
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectOut, ProjectUpdate
from app.services import project_service

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: DbSession,
    user: CurrentUser,
    q: str | None = None,
    status_filter: Annotated[ProjectStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProjectOut]:
    return project_service.list_projects(
        db, user, q, status_filter.value if status_filter else None, limit, offset
    )


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(body: ProjectCreate, db: DbSession, user: CurrentUser) -> ProjectOut:
    return project_service.create_project(db, user, body)


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: int, db: DbSession, user: CurrentUser) -> ProjectDetail:
    return project_service.get_project(db, user, project_id)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int, body: ProjectUpdate, db: DbSession, user: CurrentUser
) -> ProjectOut:
    return project_service.update_project(db, user, project_id, body)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: DbSession, user: CurrentUser) -> Response:
    project_service.delete_project(db, user, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
