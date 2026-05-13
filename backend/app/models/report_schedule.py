from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ReportScheduleFrequency, Severity

if TYPE_CHECKING:
    from app.models.user import User


class ReportSchedule(Base):
    __tablename__ = "report_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    min_severity: Mapped[Severity] = mapped_column(
        Enum(Severity, native_enum=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=Severity.medium,
    )
    frequency: Mapped[ReportScheduleFrequency] = mapped_column(
        Enum(ReportScheduleFrequency, native_enum=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ReportScheduleFrequency.daily,
    )
    recipient_email: Mapped[str] = mapped_column(String(320), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default="true")
    # HH:MM UTC; null = legacy “any time” (interval-only gating)
    preferred_time_utc: Mapped[str | None] = mapped_column(String(5), nullable=True)
    # 0=Monday … 6=Sunday (Python weekday); only used when frequency is weekly
    weekly_day_utc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="report_schedules")
