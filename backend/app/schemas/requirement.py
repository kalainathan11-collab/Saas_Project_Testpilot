"""Requirement request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import RequirementPriority, RequirementStatus


class _RequirementFields(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: RequirementPriority = RequirementPriority.MEDIUM
    status: RequirementStatus = RequirementStatus.PROPOSED

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class RequirementCreate(_RequirementFields):
    project_id: int


class RequirementUpdate(_RequirementFields):
    """Full editable field set; project_id is immutable."""


class LinkedTestCase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: str


class RequirementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None
    priority: str
    status: str
    test_case_count: int = 0
    created_at: datetime
    updated_at: datetime


class RequirementDetail(RequirementRead):
    test_cases: list[LinkedTestCase] = []
