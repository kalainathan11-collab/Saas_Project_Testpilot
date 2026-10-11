"""Dashboard summary and project reports."""

from typing import Literal

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.dependencies import CurrentUser, DbSession
from app.schemas.dashboard import DashboardSummary, ProjectReportRow
from app.services import dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/api/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    user: CurrentUser,
    db: DbSession,
    project_id: int | None = Query(default=None),
) -> DashboardSummary:
    return dashboard_service.get_summary(db, user.id, project_id)


@router.get("/api/reports/projects", response_model=list[ProjectReportRow])
def project_report(
    user: CurrentUser,
    db: DbSession,
    project_id: int | None = Query(default=None),
    format: Literal["json", "csv"] = Query(default="json"),  # noqa: A002
) -> list[ProjectReportRow] | Response:
    rows = dashboard_service.get_project_report(db, user.id, project_id)
    if format == "csv":
        return Response(
            content=dashboard_service.report_to_csv(rows),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="project-report.csv"'},
        )
    return rows
