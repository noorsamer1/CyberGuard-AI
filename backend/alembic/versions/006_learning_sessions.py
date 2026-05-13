"""add learning exercise session tables

Revision ID: 006
Revises: 005
Create Date: 2026-04-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exercise_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_id", sa.String(length=128), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "completed", "expired", "cancelled", name="exercisesessionstatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("detection_score", sa.Float(), nullable=True),
        sa.Column("analysis_score", sa.Float(), nullable=True),
        sa.Column("response_score", sa.Float(), nullable=True),
        sa.Column("reporting_score", sa.Float(), nullable=True),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("weaknesses", sa.Text(), nullable=True),
        sa.Column("hints_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_exercise_sessions_user_id", "exercise_sessions", ["user_id"])
    op.create_index("ix_exercise_sessions_scenario_id", "exercise_sessions", ["scenario_id"])
    op.create_index("ix_exercise_sessions_status", "exercise_sessions", ["status"])

    op.create_table(
        "exercise_actions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("exercise_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "action_type",
            sa.Enum(
                "acknowledge_alert",
                "resolve_alert",
                "escalate_incident",
                "add_note",
                "request_hint",
                name="exerciseactiontype",
            ),
            nullable=False,
        ),
        sa.Column("target_type", sa.String(length=64), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_exercise_actions_session_id", "exercise_actions", ["session_id"])
    op.create_index("ix_exercise_actions_user_id", "exercise_actions", ["user_id"])
    op.create_index("ix_exercise_actions_action_type", "exercise_actions", ["action_type"])


def downgrade() -> None:
    op.drop_index("ix_exercise_actions_action_type", "exercise_actions")
    op.drop_index("ix_exercise_actions_user_id", "exercise_actions")
    op.drop_index("ix_exercise_actions_session_id", "exercise_actions")
    op.drop_table("exercise_actions")

    op.drop_index("ix_exercise_sessions_status", "exercise_sessions")
    op.drop_index("ix_exercise_sessions_scenario_id", "exercise_sessions")
    op.drop_index("ix_exercise_sessions_user_id", "exercise_sessions")
    op.drop_table("exercise_sessions")
