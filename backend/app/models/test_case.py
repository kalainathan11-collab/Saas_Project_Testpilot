"""TestCase model."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.defect import Defect
    from app.models.project import Project
    from app.models.requirement import Requirement
    from app.models.test_result import TestResult


class TestCaseType(str, enum.Enum):
    __test__ = False  # not a pytest class
    FUNCTIONAL = "Functional"
    REGRESSION = "Regression"
    SMOKE = "Smoke"
    API = "API"
    UI = "UI"
    PERFORMANCE = "Performance"
    SECURITY = "Security"


class TestCasePriority(str, enum.Enum):
    __test__ = False
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TestCaseStatus(str, enum.Enum):
    __test__ = False
    DRAFT = "Draft"
    READY = "Ready"
    DEPRECATED = "Deprecated"


class TestCase(Base, TimestampMixin):
    __test__ = False  # prevent pytest collection
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    requirement_id: Mapped[int | None] = mapped_column(
        ForeignKey("requirements.id", ondelete="SET NULL"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    module: Mapped[str | None] = mapped_column(String(100), nullable=True)
    type: Mapped[str] = mapped_column(
        String(20),
        default=TestCaseType.FUNCTIONAL.value,
        server_default=TestCaseType.FUNCTIONAL.value,
        index=True,
        nullable=False,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default=TestCasePriority.MEDIUM.value,
        server_default=TestCasePriority.MEDIUM.value,
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=TestCaseStatus.DRAFT.value,
        server_default=TestCaseStatus.DRAFT.value,
        index=True,
        nullable=False,
    )
    preconditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(back_populates="test_cases")
    requirement: Mapped[Requirement | None] = relationship(back_populates="test_cases")
    results: Mapped[list[TestResult]] = relationship(
        back_populates="test_case", cascade="all, delete-orphan", passive_deletes=True
    )
    defects: Mapped[list[Defect]] = relationship(back_populates="test_case", passive_deletes=True)
