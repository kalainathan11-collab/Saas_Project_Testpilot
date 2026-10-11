"""TestRun model."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.test_result import TestResult


class TestRunStatus(str, enum.Enum):
    __test__ = False
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class TestRun(Base, TimestampMixin):
    __test__ = False  # prevent pytest collection
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    assignee: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=TestRunStatus.PLANNED.value,
        server_default=TestRunStatus.PLANNED.value,
        index=True,
        nullable=False,
    )

    project: Mapped[Project] = relationship(back_populates="test_runs")
    results: Mapped[list[TestResult]] = relationship(
        back_populates="test_run", cascade="all, delete-orphan", passive_deletes=True
    )
