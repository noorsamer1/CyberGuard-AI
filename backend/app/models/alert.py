from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AlertStatus, Severity


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[Optional[int]] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, native_enum=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        index=True,
    )
    rule_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, native_enum=False, values_callable=lambda obj: [e.value for e in obj]),
        default=AlertStatus.new,
        nullable=False,
        index=True,
    )
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    incident_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"), index=True
    )
    correlation_key: Mapped[Optional[str]] = mapped_column(String(256), index=True)
    attack_type: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    event_count: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

    event: Mapped[Optional["Event"]] = relationship("Event", back_populates="alerts")
    ai_classifications: Mapped[list["AIClassification"]] = relationship(
        "AIClassification",
        back_populates="alert",
        lazy="selectin",
    )
