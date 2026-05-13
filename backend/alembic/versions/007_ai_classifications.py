"""add ai event classifications

Revision ID: 007
Revises: 006
Create Date: 2026-04-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_classifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("prompt_type", sa.String(length=64), nullable=False, server_default="event_classify"),
        sa.Column("attack_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("suggested_severity", sa.String(length=16), nullable=False, server_default="low"),
        sa.Column("why_classified", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("mitre_tactics", sa.JSON(), nullable=True),
        sa.Column("mitre_techniques", sa.JSON(), nullable=True),
        sa.Column("recommended_actions", sa.JSON(), nullable=True),
        sa.Column("should_create_alert", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("event_id", name="uq_ai_classifications_event_id"),
    )
    op.create_index("ix_ai_classifications_event_id", "ai_classifications", ["event_id"])
    op.create_index("ix_ai_classifications_alert_id", "ai_classifications", ["alert_id"])
    op.create_index("ix_ai_classifications_incident_id", "ai_classifications", ["incident_id"])
    op.create_index("ix_ai_classifications_owner_id", "ai_classifications", ["owner_id"])
    op.create_index("ix_ai_classifications_attack_type", "ai_classifications", ["attack_type"])


def downgrade() -> None:
    op.drop_index("ix_ai_classifications_attack_type", "ai_classifications")
    op.drop_index("ix_ai_classifications_owner_id", "ai_classifications")
    op.drop_index("ix_ai_classifications_incident_id", "ai_classifications")
    op.drop_index("ix_ai_classifications_alert_id", "ai_classifications")
    op.drop_index("ix_ai_classifications_event_id", "ai_classifications")
    op.drop_table("ai_classifications")
