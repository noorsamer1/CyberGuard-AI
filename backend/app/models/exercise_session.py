from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ExerciseSessionStatus


class ExerciseSession(Base):
    __tablename__ = "exercise_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    scenario_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[ExerciseSessionStatus] = mapped_column(
        Enum(
            ExerciseSessionStatus,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=ExerciseSessionStatus.active,
        nullable=False,
        index=True,
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    overall_score: Mapped[Optional[float]] = mapped_column(Float)
    detection_score: Mapped[Optional[float]] = mapped_column(Float)
    analysis_score: Mapped[Optional[float]] = mapped_column(Float)
    response_score: Mapped[Optional[float]] = mapped_column(Float)
    reporting_score: Mapped[Optional[float]] = mapped_column(Float)

    strengths: Mapped[Optional[str]] = mapped_column(Text)
    weaknesses: Mapped[Optional[str]] = mapped_column(Text)
    hints_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result_json: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    actions: Mapped[list["ExerciseAction"]] = relationship(
        "ExerciseAction", back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )
