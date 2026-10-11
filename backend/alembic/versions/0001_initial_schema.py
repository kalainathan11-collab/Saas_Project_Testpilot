"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-10
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _user_fk() -> sa.Column:
    return sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("oauth_provider", sa.String(50), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        _user_fk(),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default="false", nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        _user_fk(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("key", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="Active", nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("user_id", "key", name="uq_projects_user_id_key"),
    )
    op.create_index("ix_projects_user_id", "projects", ["user_id"])
    op.create_index("ix_projects_status", "projects", ["status"])

    op.create_table(
        "requirements",
        sa.Column("id", sa.Integer(), primary_key=True),
        _user_fk(),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(20), server_default="Medium", nullable=False),
        sa.Column("status", sa.String(20), server_default="Proposed", nullable=False),
        *_timestamps(),
    )
    for col in ("user_id", "project_id", "priority", "status"):
        op.create_index(f"ix_requirements_{col}", "requirements", [col])

    op.create_table(
        "test_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        _user_fk(),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requirement_id", sa.Integer(), sa.ForeignKey("requirements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("module", sa.String(100), nullable=True),
        sa.Column("type", sa.String(20), server_default="Functional", nullable=False),
        sa.Column("priority", sa.String(20), server_default="Medium", nullable=False),
        sa.Column("status", sa.String(20), server_default="Draft", nullable=False),
        sa.Column("preconditions", sa.Text(), nullable=True),
        sa.Column("steps", sa.Text(), nullable=True),
        sa.Column("expected_result", sa.Text(), nullable=True),
        *_timestamps(),
    )
    for col in ("user_id", "project_id", "requirement_id", "type", "priority", "status"):
        op.create_index(f"ix_test_cases_{col}", "test_cases", [col])

    op.create_table(
        "test_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        _user_fk(),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("assignee", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), server_default="Planned", nullable=False),
        *_timestamps(),
    )
    for col in ("user_id", "project_id", "status"):
        op.create_index(f"ix_test_runs_{col}", "test_runs", [col])

    op.create_table(
        "test_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        _user_fk(),
        sa.Column("test_run_id", sa.Integer(), sa.ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_case_id", sa.Integer(), sa.ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("test_run_id", "test_case_id", name="uq_test_results_run_case"),
    )
    for col in ("user_id", "test_run_id", "test_case_id", "status"):
        op.create_index(f"ix_test_results_{col}", "test_results", [col])

    op.create_table(
        "defects",
        sa.Column("id", sa.Integer(), primary_key=True),
        _user_fk(),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_case_id", sa.Integer(), sa.ForeignKey("test_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), server_default="Major", nullable=False),
        sa.Column("status", sa.String(20), server_default="Open", nullable=False),
        sa.Column("assignee", sa.String(100), nullable=True),
        *_timestamps(),
    )
    for col in ("user_id", "project_id", "test_case_id", "severity", "status"):
        op.create_index(f"ix_defects_{col}", "defects", [col])


def downgrade() -> None:
    for table in (
        "defects", "test_results", "test_runs", "test_cases",
        "requirements", "projects", "refresh_tokens", "users",
    ):
        op.drop_table(table)
