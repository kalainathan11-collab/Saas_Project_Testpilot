"""Dashboard and reports response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResultCounts(BaseModel):
    Passed: int = 0
    Failed: int = 0
    Blocked: int = 0
    Skipped: int = 0


class SeverityCounts(BaseModel):
    Minor: int = 0
    Major: int = 0
    Critical: int = 0
    Blocker: int = 0


class RunProgress(BaseModel):
    id: int
    name: str
    progress_pct: int


class RecentDefect(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    test_case_id: int | None
    title: str
    description: str | None
    severity: str
    status: str
    assignee: str | None
    created_at: datetime
    updated_at: datetime


class DashboardSummary(BaseModel):
    test_cases: int
    test_runs: int
    executed: int
    pass_rate: int
    open_defects: int
    results: ResultCounts
    defects_by_severity: SeverityCounts
    runs: list[RunProgress]
    recent_defects: list[RecentDefect]


class ProjectReportRow(BaseModel):
    project_id: int
    project: str
    test_cases: int
    requirements: int
    coverage_pct: int
    runs: int
    executed: int
    pass_rate: int
    open_defects: int
    defects: int
