"""Project request/response schemas."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models import ProjectStatus

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Key = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]


class ProjectBase(BaseModel):
    name: Name
    key: Key
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE

    @field_validator("key")
    @classmethod
    def _upper_key(cls, value: str) -> str:
        return value.upper()


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    pass


class ProjectCounts(BaseModel):
    requirements: int = 0
    test_cases: int = 0
    test_runs: int = 0
    defects: int = 0


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    key: str
    description: str | None = None
    status: str
    owner: str | None = None
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectOut):
    counts: ProjectCounts = Field(default_factory=ProjectCounts)
