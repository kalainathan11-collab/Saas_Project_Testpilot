"""Pydantic schemas for the test runs module."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models import TestResultStatus, TestRunStatus


class TestRunBase(BaseModel):
    __test__ = False
    name: str = Field(min_length=1, max_length=200)
    assignee: str | None = Field(default=None, max_length=100)
    # Accepted for client compatibility; the stored status is always derived from results.
    status: TestRunStatus | None = None

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v


class TestRunCreate(TestRunBase):
    __test__ = False
    project_id: int


class TestRunUpdate(TestRunBase):
    __test__ = False
    project_id: int | None = None


class TestRunResultIn(BaseModel):
    __test__ = False
    status: TestResultStatus
    comment: str | None = Field(default=None, max_length=10000)


class TestRunResultOut(BaseModel):
    __test__ = False
    status: str
    comment: str | None
    executed_at: datetime | None


class TestRunCaseOut(BaseModel):
    __test__ = False
    id: int
    title: str
    priority: str
    steps: str | None
    expected_result: str | None
    result: TestRunResultOut | None


class TestRunOut(BaseModel):
    __test__ = False
    id: int
    project_id: int
    name: str
    assignee: str | None
    status: str
    total_cases: int
    executed: int
    passed: int
    created_at: datetime
    updated_at: datetime


class TestRunDetailOut(TestRunOut):
    __test__ = False
    cases: list[TestRunCaseOut]
