"""Dashboard and report aggregation (user-scoped, grouped SQL, no N+1)."""

import csv
import io
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import (
    Defect,
    DefectStatus,
    Project,
    Requirement,
    TestCase,
    TestCaseStatus,
    TestResult,
    TestResultStatus,
    TestRun,
)
from app.schemas.dashboard import (
    DashboardSummary,
    ProjectReportRow,
    RecentDefect,
    ResultCounts,
    RunProgress,
    SeverityCounts,
)

RUN_LIST_LIMIT = 10
RECENT_DEFECTS = 5
_OPEN_STATUSES = (DefectStatus.OPEN.value, DefectStatus.IN_PROGRESS.value)
_CSV_COLUMNS = [
    "project_id",
    "project",
    "test_cases",
    "requirements",
    "coverage_pct",
    "runs",
    "executed",
    "pass_rate",
    "open_defects",
    "defects",
]


def pct(part: int, whole: int) -> int:
    """Zero-safe integer percentage, clamped to 0-100."""
    if whole <= 0:
        return 0
    return max(0, min(100, round(part * 100 / whole)))


def _ensure_project(db: Session, user_id: int, project_id: int) -> None:
    owned = db.scalar(
        select(Project.id).where(Project.id == project_id, Project.user_id == user_id)
    )
    if owned is None:
        raise NotFoundError("Project")


def get_summary(db: Session, user_id: int, project_id: int | None) -> DashboardSummary:
    if project_id is not None:
        _ensure_project(db, user_id, project_id)

    def scoped(stmt: Any, model: Any) -> Any:
        stmt = stmt.where(model.user_id == user_id)
        if project_id is not None:
            stmt = stmt.where(model.project_id == project_id)
        return stmt

    test_cases = db.scalar(scoped(select(func.count(TestCase.id)), TestCase)) or 0
    test_runs = db.scalar(scoped(select(func.count(TestRun.id)), TestRun)) or 0

    # Results of the user's runs, grouped by status (joined to run for project scope).
    res_stmt = (
        select(TestResult.status, func.count(TestResult.id))
        .join(TestRun, TestRun.id == TestResult.test_run_id)
        .where(TestRun.user_id == user_id, TestResult.user_id == user_id)
        .group_by(TestResult.status)
    )
    if project_id is not None:
        res_stmt = res_stmt.where(TestRun.project_id == project_id)
    by_status = {s: int(n) for s, n in db.execute(res_stmt).all()}
    results = ResultCounts(**{s.value: by_status.get(s.value, 0) for s in TestResultStatus})
    executed = sum(by_status.values())
    pass_rate = pct(results.Passed, executed)

    # Defects by severity + open count in one grouped query.
    open_flag = case((Defect.status.in_(_OPEN_STATUSES), 1), else_=0)
    def_rows = db.execute(
        scoped(
            select(Defect.severity, func.count(Defect.id), func.sum(open_flag)),
            Defect,
        ).group_by(Defect.severity)
    ).all()
    sev: dict[str, int] = {}
    open_defects = 0
    for severity, total, opened in def_rows:
        sev[severity] = int(total)
        open_defects += int(opened or 0)
    severity_counts = SeverityCounts(**{k: sev.get(k, 0) for k in SeverityCounts.model_fields})

    recent = db.scalars(
        scoped(select(Defect), Defect).order_by(Defect.id.desc()).limit(RECENT_DEFECTS)
    ).all()

    # Run progress: results on in-scope (non-deprecated) cases / such cases in the project.
    runs = db.execute(
        scoped(select(TestRun.id, TestRun.name, TestRun.project_id), TestRun)
        .order_by(TestRun.id.desc())
        .limit(RUN_LIST_LIMIT)
    ).all()
    run_ids = [r.id for r in runs]
    project_ids = {r.project_id for r in runs}
    scope_counts: dict[int, int] = {}
    done_counts: dict[int, int] = {}
    if run_ids:
        scope_counts = {
            int(pid): int(n)
            for pid, n in db.execute(
                select(TestCase.project_id, func.count(TestCase.id))
                .where(
                    TestCase.user_id == user_id,
                    TestCase.project_id.in_(project_ids),
                    TestCase.status != TestCaseStatus.DEPRECATED.value,
                )
                .group_by(TestCase.project_id)
            ).all()
        }
        done_counts = {
            int(rid): int(n)
            for rid, n in db.execute(
                select(TestResult.test_run_id, func.count(TestResult.id))
                .join(TestCase, TestCase.id == TestResult.test_case_id)
                .where(
                    TestResult.user_id == user_id,
                    TestResult.test_run_id.in_(run_ids),
                    TestCase.status != TestCaseStatus.DEPRECATED.value,
                )
                .group_by(TestResult.test_run_id)
            ).all()
        }
    run_progress = [
        RunProgress(
            id=r.id,
            name=r.name,
            progress_pct=pct(done_counts.get(r.id, 0), scope_counts.get(r.project_id, 0)),
        )
        for r in runs
    ]

    return DashboardSummary(
        test_cases=test_cases,
        test_runs=test_runs,
        executed=executed,
        pass_rate=pass_rate,
        open_defects=open_defects,
        results=results,
        defects_by_severity=severity_counts,
        runs=run_progress,
        recent_defects=[RecentDefect.model_validate(d) for d in recent],
    )


def get_project_report(db: Session, user_id: int, project_id: int | None) -> list[ProjectReportRow]:
    if project_id is not None:
        _ensure_project(db, user_id, project_id)

    proj_stmt = select(Project.id, Project.name).where(Project.user_id == user_id)
    if project_id is not None:
        proj_stmt = proj_stmt.where(Project.id == project_id)
    projects = db.execute(proj_stmt.order_by(Project.id)).all()
    if not projects:
        return []
    ids = [p.id for p in projects]

    def grouped(stmt: Any, col: Any) -> dict[int, int]:
        return {int(k): int(v or 0) for k, v in db.execute(stmt.group_by(col)).all()}

    cases = grouped(
        select(TestCase.project_id, func.count(TestCase.id)).where(
            TestCase.user_id == user_id, TestCase.project_id.in_(ids)
        ),
        TestCase.project_id,
    )
    reqs = grouped(
        select(Requirement.project_id, func.count(Requirement.id)).where(
            Requirement.user_id == user_id, Requirement.project_id.in_(ids)
        ),
        Requirement.project_id,
    )
    covered = grouped(
        select(TestCase.project_id, func.count(func.distinct(TestCase.requirement_id))).where(
            TestCase.user_id == user_id,
            TestCase.project_id.in_(ids),
            TestCase.requirement_id.is_not(None),
        ),
        TestCase.project_id,
    )
    runs = grouped(
        select(TestRun.project_id, func.count(TestRun.id)).where(
            TestRun.user_id == user_id, TestRun.project_id.in_(ids)
        ),
        TestRun.project_id,
    )
    passed_flag = case((TestResult.status == TestResultStatus.PASSED.value, 1), else_=0)
    res_rows = db.execute(
        select(TestRun.project_id, func.count(TestResult.id), func.sum(passed_flag))
        .join(TestRun, TestRun.id == TestResult.test_run_id)
        .where(
            TestRun.user_id == user_id,
            TestResult.user_id == user_id,
            TestRun.project_id.in_(ids),
        )
        .group_by(TestRun.project_id)
    ).all()
    executed = {int(pid): int(n) for pid, n, _ in res_rows}
    passed = {int(pid): int(p or 0) for pid, _, p in res_rows}
    open_flag = case((Defect.status.in_(_OPEN_STATUSES), 1), else_=0)
    def_rows = db.execute(
        select(Defect.project_id, func.count(Defect.id), func.sum(open_flag))
        .where(Defect.user_id == user_id, Defect.project_id.in_(ids))
        .group_by(Defect.project_id)
    ).all()
    defects = {int(pid): int(n) for pid, n, _ in def_rows}
    open_def = {int(pid): int(o or 0) for pid, _, o in def_rows}

    return [
        ProjectReportRow(
            project_id=p.id,
            project=p.name,
            test_cases=cases.get(p.id, 0),
            requirements=reqs.get(p.id, 0),
            coverage_pct=pct(covered.get(p.id, 0), reqs.get(p.id, 0)),
            runs=runs.get(p.id, 0),
            executed=executed.get(p.id, 0),
            pass_rate=pct(passed.get(p.id, 0), executed.get(p.id, 0)),
            open_defects=open_def.get(p.id, 0),
            defects=defects.get(p.id, 0),
        )
        for p in projects
    ]


def csv_safe(value: object) -> str:
    """Neutralise spreadsheet formula injection."""
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


def report_to_csv(rows: list[ProjectReportRow]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow(_CSV_COLUMNS)
    for row in rows:
        data = row.model_dump()
        writer.writerow([csv_safe(data[c]) for c in _CSV_COLUMNS])
    return buf.getvalue()
