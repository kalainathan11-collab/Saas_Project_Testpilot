"""Model package: importing it registers every table on Base.metadata."""

from app.models.base import Base, TimestampMixin
from app.models.defect import Defect, DefectSeverity, DefectStatus
from app.models.project import Project, ProjectStatus
from app.models.refresh_token import RefreshToken
from app.models.requirement import Requirement, RequirementPriority, RequirementStatus
from app.models.test_case import TestCase, TestCasePriority, TestCaseStatus, TestCaseType
from app.models.test_result import TestResult, TestResultStatus
from app.models.test_run import TestRun, TestRunStatus
from app.models.user import User

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "RefreshToken",
    "Project",
    "ProjectStatus",
    "Requirement",
    "RequirementPriority",
    "RequirementStatus",
    "TestCase",
    "TestCaseType",
    "TestCasePriority",
    "TestCaseStatus",
    "TestRun",
    "TestRunStatus",
    "TestResult",
    "TestResultStatus",
    "Defect",
    "DefectSeverity",
    "DefectStatus",
]
