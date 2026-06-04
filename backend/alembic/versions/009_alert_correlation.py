"""add alert correlation fields

Revision ID: 009
Revises: 008
Create Date: 2026-05-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("incident_id", sa.Integer(), nullable=True))
    op.add_column("alerts", sa.Column("correlation_key", sa.String(length=256), nullable=True))
    op.add_column("alerts", sa.Column("attack_type", sa.String(length=64), nullable=True))
    op.add_column(
        "alerts",
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column("alerts", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_alerts_incident_id",
        "alerts",
        "incidents",
        ["incident_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_alerts_incident_id", "alerts", ["incident_id"])
    op.create_index("ix_alerts_correlation_key", "alerts", ["correlation_key"])
    op.create_index("ix_alerts_attack_type", "alerts", ["attack_type"])


def downgrade() -> None:
    op.drop_index("ix_alerts_attack_type", table_name="alerts")
    op.drop_index("ix_alerts_correlation_key", table_name="alerts")
    op.drop_index("ix_alerts_incident_id", table_name="alerts")
    op.drop_constraint("fk_alerts_incident_id", "alerts", type_="foreignkey")
    op.drop_column("alerts", "last_seen_at")
    op.drop_column("alerts", "event_count")
    op.drop_column("alerts", "attack_type")
    op.drop_column("alerts", "correlation_key")
    op.drop_column("alerts", "incident_id")
