"""report_schedules preferred run time (UTC)

Revision ID: 004
Revises: 003
Create Date: 2026-04-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "report_schedules",
        sa.Column("preferred_time_utc", sa.String(length=5), nullable=True),
    )
    op.add_column(
        "report_schedules",
        sa.Column("weekly_day_utc", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("report_schedules", "weekly_day_utc")
    op.drop_column("report_schedules", "preferred_time_utc")
