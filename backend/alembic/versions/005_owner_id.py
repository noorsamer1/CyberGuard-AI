"""add owner_id to events, alerts, incidents

Revision ID: 005
Revises: 004
Create Date: 2026-04-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("events", sa.Column("owner_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_events_owner_id", "events", "users", ["owner_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_events_owner_id", "events", ["owner_id"])

    op.add_column("alerts", sa.Column("owner_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_alerts_owner_id", "alerts", "users", ["owner_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_alerts_owner_id", "alerts", ["owner_id"])

    op.add_column("incidents", sa.Column("owner_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_incidents_owner_id", "incidents", "users", ["owner_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_incidents_owner_id", "incidents", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_incidents_owner_id", "incidents")
    op.drop_constraint("fk_incidents_owner_id", "incidents", type_="foreignkey")
    op.drop_column("incidents", "owner_id")

    op.drop_index("ix_alerts_owner_id", "alerts")
    op.drop_constraint("fk_alerts_owner_id", "alerts", type_="foreignkey")
    op.drop_column("alerts", "owner_id")

    op.drop_index("ix_events_owner_id", "events")
    op.drop_constraint("fk_events_owner_id", "events", type_="foreignkey")
    op.drop_column("events", "owner_id")
