"""Requirements CRUD router (/api/requirements)."""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.dependencies import CurrentUser, DbSession
from app.models import RequirementPriority, RequirementStatus
from app.schemas.requirement import (
    RequirementCreate,
    RequirementDetail,
    RequirementRead,
    RequirementUpdate,
)
from app.services import requirement_service

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


@router.get("", response_model=list[RequirementRead])
def list_requirements(
    user: CurrentUser,
    db: DbSession,
    project_id: int | None = None,
    priority: RequirementPriority | None = None,
    status_filter: Annotated[RequirementStatus | None, Query(alias="status")] = None,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[RequirementRead]:
    return requirement_service.list_requirements(
        db,
        user.id,
        project_id=project_id,
        priority=priority,
        status=status_filter,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=RequirementRead, status_code=status.HTTP_201_CREATED)
def create_requirement(
    body: RequirementCreate, user: CurrentUser, db: DbSession
) -> RequirementRead:
    return requirement_service.create_requirement(db, user.id, body)


@router.get("/{requirement_id}", response_model=RequirementDetail)
def get_requirement(requirement_id: int, user: CurrentUser, db: DbSession) -> RequirementDetail:
    return requirement_service.get_requirement(db, user.id, requirement_id)


@router.put("/{requirement_id}", response_model=RequirementRead)
def update_requirement(
    requirement_id: int, body: RequirementUpdate, user: CurrentUser, db: DbSession
) -> RequirementRead:
    return requirement_service.update_requirement(db, user.id, requirement_id, body)


@router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_requirement(requirement_id: int, user: CurrentUser, db: DbSession) -> Response:
    requirement_service.delete_requirement(db, user.id, requirement_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
