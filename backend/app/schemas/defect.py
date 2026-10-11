"""Pydantic schemas for defects."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import DefectSeverity, DefectStatus


class DefectBase(BaseModel):
    project_id: int
    test_case_id: int | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    severity: DefectSeverity = DefectSeverity.MAJOR
    status: DefectStatus = DefectStatus.OPEN
    assignee: str | None = Field(default=None, max_length=100)


class DefectCreate(DefectBase):
    pass


class DefectUpdate(DefectBase):
    """Full editable field set (PUT)."""


class DefectRead(BaseModel):
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
