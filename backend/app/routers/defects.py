"""Defects CRUD endpoints (/api/defects)."""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.dependencies import CurrentUser, DbSession
from app.models import DefectSeverity, DefectStatus
from app.schemas.defect import DefectCreate, DefectRead, DefectUpdate
from app.services import defect_service

router = APIRouter(prefix="/api/defects", tags=["defects"])


@router.get("", response_model=list[DefectRead])
def list_defects(
    user: CurrentUser,
    db: DbSession,
    project_id: int | None = None,
    severity: DefectSeverity | None = None,
    status_: Annotated[DefectStatus | None, Query(alias="status")] = None,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DefectRead]:
    rows = defect_service.list_defects(
        db,
        user.id,
        project_id=project_id,
        severity=severity.value if severity else None,
        status=status_.value if status_ else None,
        q=q,
        limit=limit,
        offset=offset,
    )
    return [DefectRead.model_validate(r) for r in rows]


@router.post("", response_model=DefectRead, status_code=status.HTTP_201_CREATED)
def create_defect(body: DefectCreate, user: CurrentUser, db: DbSession) -> DefectRead:
    return DefectRead.model_validate(defect_service.create_defect(db, user.id, body))


@router.get("/{defect_id}", response_model=DefectRead)
def get_defect(defect_id: int, user: CurrentUser, db: DbSession) -> DefectRead:
    return DefectRead.model_validate(defect_service.get_defect(db, user.id, defect_id))


@router.put("/{defect_id}", response_model=DefectRead)
def update_defect(
    defect_id: int, body: DefectUpdate, user: CurrentUser, db: DbSession
) -> DefectRead:
    return DefectRead.model_validate(defect_service.update_defect(db, user.id, defect_id, body))


@router.delete("/{defect_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_defect(defect_id: int, user: CurrentUser, db: DbSession) -> Response:
    defect_service.delete_defect(db, user.id, defect_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
