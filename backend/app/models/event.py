from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func  # noqa: F401
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Severity


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    source_ip: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    destination_ip: Mapped[Optional[str]] = mapped_column(String(64))
    username: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(64))
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, native_enum=False, values_callable=lambda obj: [e.value for e in obj]),
        default=Severity.low,
        nullable=False,
        index=True,
    )
    message: Mapped[Optional[str]] = mapped_column(Text)
    protocol: Mapped[Optional[str]] = mapped_column(String(32))
    port: Mapped[Optional[int]] = mapped_column(Integer)
    raw_log: Mapped[Optional[str]] = mapped_column(Text)
    source_system: Mapped[Optional[str]] = mapped_column(String(128))
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="event")
    ai_classification: Mapped[Optional["AIClassification"]] = relationship(
        "AIClassification",
        back_populates="event",
        lazy="selectin",
        uselist=False,
    )
