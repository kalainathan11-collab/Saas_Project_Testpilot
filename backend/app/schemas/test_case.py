"""Pydantic schemas for test cases."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TestCasePriority, TestCaseStatus, TestCaseType


class TestCaseBase(BaseModel):
    __test__ = False

    requirement_id: int | None = None
    title: str = Field(min_length=1, max_length=255)
    module: str | None = Field(default=None, max_length=100)
    type: TestCaseType = TestCaseType.FUNCTIONAL
    priority: TestCasePriority = TestCasePriority.MEDIUM
    status: TestCaseStatus = TestCaseStatus.DRAFT
    preconditions: str | None = None
    steps: str | None = None
    expected_result: str | None = None

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class TestCaseCreate(TestCaseBase):
    __test__ = False

    project_id: int


class TestCaseUpdate(TestCaseBase):
    """Full editable field set (PUT). project_id may be omitted to keep it."""

    __test__ = False

    project_id: int | None = None


class TestCaseOut(BaseModel):
    __test__ = False
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    requirement_id: int | None
    title: str
    module: str | None
    type: str
    priority: str
    status: str
    preconditions: str | None
    steps: str | None
    expected_result: str | None
    created_at: datetime
    updated_at: datetime
