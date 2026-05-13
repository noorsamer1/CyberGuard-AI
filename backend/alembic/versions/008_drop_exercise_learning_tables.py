"""drop learning exercise session tables and enum types

Revision ID: 008
Revises: 007
Create Date: 2026-05-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "exercise_actions" in tables:
        op.drop_index("ix_exercise_actions_action_type", table_name="exercise_actions")
        op.drop_index("ix_exercise_actions_user_id", table_name="exercise_actions")
        op.drop_index("ix_exercise_actions_session_id", table_name="exercise_actions")
        op.drop_table("exercise_actions")

    if "exercise_sessions" in tables:
        op.drop_index("ix_exercise_sessions_status", table_name="exercise_sessions")
        op.drop_index("ix_exercise_sessions_scenario_id", table_name="exercise_sessions")
        op.drop_index("ix_exercise_sessions_user_id", table_name="exercise_sessions")
        op.drop_table("exercise_sessions")

    if bind.dialect.name == "postgresql":
        op.execute(sa.text("DROP TYPE IF EXISTS exerciseactiontype"))
        op.execute(sa.text("DROP TYPE IF EXISTS exercisesessionstatus"))


def downgrade() -> None:
    """Learning Lab tables removed; downgrade intentionally omitted."""
