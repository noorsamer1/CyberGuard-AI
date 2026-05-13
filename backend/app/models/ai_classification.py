from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class AIClassification(Base):
    __tablename__ = "ai_classifications"
    __table_args__ = (UniqueConstraint("event_id", name="uq_ai_classifications_event_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    alert_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alerts.id", ondelete="SET NULL"), index=True)
    incident_id: Mapped[Optional[int]] = mapped_column(ForeignKey("incidents.id", ondelete="SET NULL"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_type: Mapped[str] = mapped_column(String(64), nullable=False, default="event_classify")
    attack_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    suggested_severity: Mapped[str] = mapped_column(String(16), nullable=False, default="low")
    why_classified: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_json: Mapped[list[str] | None] = mapped_column("evidence", JSON)
    mitre_tactics_json: Mapped[list[str] | None] = mapped_column("mitre_tactics", JSON)
    mitre_techniques_json: Mapped[list[str] | None] = mapped_column("mitre_techniques", JSON)
    recommended_actions_json: Mapped[list[str] | None] = mapped_column("recommended_actions", JSON)
    should_create_alert: Mapped[bool] = mapped_column(default=False, nullable=False)
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    event: Mapped["Event"] = relationship("Event", back_populates="ai_classification")
    alert: Mapped[Optional["Alert"]] = relationship("Alert", back_populates="ai_classifications")
