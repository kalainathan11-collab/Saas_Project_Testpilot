"""Business logic for test runs and their results."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import ColumnElement, case, delete, func, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import (
    Project,
    TestCase,
    TestCaseStatus,
    TestResult,
    TestResultStatus,
    TestRun,
    TestRunStatus,
)
from app.schemas.test_run import (
    TestRunCaseOut,
    TestRunCreate,
    TestRunDetailOut,
    TestRunOut,
    TestRunResultIn,
    TestRunResultOut,
    TestRunUpdate,
)
from app.services.common import LIKE_ESCAPE, like_pattern


def derive_status(total: int, executed: int) -> str:
    """Planned: nothing executed; Completed: every in-scope case executed."""
    if executed == 0:
        return TestRunStatus.PLANNED.value
    if total > 0 and executed >= total:
        return TestRunStatus.COMPLETED.value
    return TestRunStatus.IN_PROGRESS.value


class TestRunService:
    __test__ = False

    def __init__(self, db: Session, user_id: int) -> None:
        self.db = db
        self.user_id = user_id

    # ---------- helpers ----------
    def _in_scope(self) -> tuple[ColumnElement[bool], ColumnElement[bool]]:
        return (
            TestCase.user_id == self.user_id,
            TestCase.status != TestCaseStatus.DEPRECATED.value,
        )

    def _totals(self, project_ids: set[int]) -> dict[int, int]:
        if not project_ids:
            return {}
        rows = self.db.execute(
            select(TestCase.project_id, func.count(TestCase.id))
            .where(TestCase.project_id.in_(project_ids), *self._in_scope())
            .group_by(TestCase.project_id)
        ).all()
        return {int(pid): int(n) for pid, n in rows}

    def _result_counts(self, run_ids: list[int]) -> dict[int, tuple[int, int]]:
        """run_id -> (executed, passed), counting only in-scope cases."""
        if not run_ids:
            return {}
        rows = self.db.execute(
            select(
                TestResult.test_run_id,
                func.count(TestResult.id),
                func.coalesce(
                    func.sum(
                        case((TestResult.status == TestResultStatus.PASSED.value, 1), else_=0)
                    ),
                    0,
                ),
            )
            .join(TestCase, TestCase.id == TestResult.test_case_id)
            .where(TestResult.test_run_id.in_(run_ids), *self._in_scope())
            .group_by(TestResult.test_run_id)
        ).all()
        return {int(rid): (int(e), int(p)) for rid, e, p in rows}

    def _to_out(self, runs: list[TestRun]) -> list[TestRunOut]:
        totals = self._totals({r.project_id for r in runs})
        counts = self._result_counts([r.id for r in runs])
        out: list[TestRunOut] = []
        for r in runs:
            total = totals.get(r.project_id, 0)
            executed, passed = counts.get(r.id, (0, 0))
            out.append(
                TestRunOut(
                    id=r.id,
                    project_id=r.project_id,
                    name=r.name,
                    assignee=r.assignee,
                    status=derive_status(total, executed),
                    total_cases=total,
                    executed=executed,
                    passed=passed,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                )
            )
        return out

    def _sync_status(self, run: TestRun) -> None:
        """Recompute and persist the run's status from its results."""
        total = self._totals({run.project_id}).get(run.project_id, 0)
        executed, _ = self._result_counts([run.id]).get(run.id, (0, 0))
        run.status = derive_status(total, executed)

    def _project(self, project_id: int) -> Project:
        project = self.db.scalar(
            select(Project).where(Project.id == project_id, Project.user_id == self.user_id)
        )
        if project is None:
            raise NotFoundError("Project")
        return project

    def _get(self, run_id: int) -> TestRun:
        run = self.db.scalar(
            select(TestRun).where(TestRun.id == run_id, TestRun.user_id == self.user_id)
        )
        if run is None:
            raise NotFoundError("Test run")
        return run

    # ---------- queries ----------
    def list(
        self,
        project_id: int | None,
        status: TestRunStatus | None,
        q: str | None,
        limit: int,
        offset: int,
    ) -> list[TestRunOut]:
        stmt = select(TestRun).where(TestRun.user_id == self.user_id)
        if project_id is not None:
            stmt = stmt.where(TestRun.project_id == project_id)
        if status is not None:
            stmt = stmt.where(TestRun.status == status.value)
        if q and q.strip():
            like = like_pattern(q).lower()
            stmt = stmt.where(
                func.lower(TestRun.name).like(like, escape=LIKE_ESCAPE)
                | func.lower(func.coalesce(TestRun.assignee, "")).like(like, escape=LIKE_ESCAPE)
            )
        stmt = stmt.order_by(TestRun.id.desc()).limit(limit).offset(offset)
        return self._to_out(list(self.db.scalars(stmt).all()))

    def detail(self, run_id: int) -> TestRunDetailOut:
        run = self._get(run_id)
        base = self._to_out([run])[0]
        if run.status != base.status:  # heal drift (e.g. a case was deprecated)
            run.status = base.status
            self.db.commit()
        cases = self.db.scalars(
            select(TestCase)
            .where(TestCase.project_id == run.project_id, *self._in_scope())
            .order_by(TestCase.id)
        ).all()
        results = {
            r.test_case_id: r
            for r in self.db.scalars(select(TestResult).where(TestResult.test_run_id == run.id))
        }
        items: list[TestRunCaseOut] = []
        for c in cases:
            res = results.get(c.id)
            items.append(
                TestRunCaseOut(
                    id=c.id,
                    title=c.title,
                    priority=c.priority,
                    steps=c.steps,
                    expected_result=c.expected_result,
                    result=TestRunResultOut(
                        status=res.status, comment=res.comment, executed_at=res.executed_at
                    )
                    if res
                    else None,
                )
            )
        return TestRunDetailOut(**base.model_dump(), cases=items)

    # ---------- mutations ----------
    def create(self, data: TestRunCreate) -> TestRunDetailOut:
        self._project(data.project_id)
        run = TestRun(
            user_id=self.user_id,
            project_id=data.project_id,
            name=data.name,
            assignee=data.assignee,
            status=TestRunStatus.PLANNED.value,
        )
        self.db.add(run)
        self.db.flush()
        self._sync_status(run)
        self.db.commit()
        return self.detail(run.id)

    def update(self, run_id: int, data: TestRunUpdate) -> TestRunDetailOut:
        run = self._get(run_id)
        if data.project_id is not None and data.project_id != run.project_id:
            self._project(data.project_id)
            # Results belong to the old project's cases; drop them.
            self.db.execute(delete(TestResult).where(TestResult.test_run_id == run.id))
            run.project_id = data.project_id
        run.name = data.name
        run.assignee = data.assignee
        self.db.flush()
        self._sync_status(run)
        self.db.commit()
        return self.detail(run.id)

    def delete(self, run_id: int) -> None:
        run = self._get(run_id)
        self.db.execute(delete(TestResult).where(TestResult.test_run_id == run.id))
        self.db.delete(run)
        self.db.commit()

    def upsert_result(self, run_id: int, case_id: int, data: TestRunResultIn) -> TestRunDetailOut:
        run = self._get(run_id)
        tc = self.db.scalar(
            select(TestCase).where(
                TestCase.id == case_id,
                TestCase.project_id == run.project_id,
                *self._in_scope(),
            )
        )
        if tc is None:
            raise NotFoundError("Test case")
        now = datetime.now(UTC)
        result = self.db.scalar(
            select(TestResult).where(
                TestResult.test_run_id == run.id, TestResult.test_case_id == case_id
            )
        )
        if result is None:
            result = TestResult(
                user_id=self.user_id,
                test_run_id=run.id,
                test_case_id=case_id,
                status=data.status.value,
            )
            self.db.add(result)
        result.status = data.status.value
        result.comment = data.comment
        result.executed_at = now
        self.db.flush()
        self._sync_status(run)
        run.updated_at = now
        self.db.commit()
        return self.detail(run.id)

    def clear_results(self, run_id: int) -> None:
        run = self._get(run_id)
        self.db.execute(delete(TestResult).where(TestResult.test_run_id == run.id))
        run.status = TestRunStatus.PLANNED.value
        run.updated_at = datetime.now(UTC)
        self.db.commit()
