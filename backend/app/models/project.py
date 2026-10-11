"""Project model."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.defect import Defect
    from app.models.requirement import Requirement
    from app.models.test_case import TestCase
    from app.models.test_run import TestRun


class ProjectStatus(str, enum.Enum):
    ACTIVE = "Active"
    ON_HOLD = "On Hold"
    ARCHIVED = "Archived"


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_projects_user_id_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ProjectStatus.ACTIVE.value,
        server_default=ProjectStatus.ACTIVE.value,
        index=True,
        nullable=False,
    )

    requirements: Mapped[list[Requirement]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )
    test_cases: Mapped[list[TestCase]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )
    test_runs: Mapped[list[TestRun]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )
    defects: Mapped[list[Defect]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )
