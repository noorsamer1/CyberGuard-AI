from datetime import datetime
import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import ReportScheduleFrequency, Severity

_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class ReportScheduleCreate(BaseModel):
    min_severity: Severity = Severity.medium
    frequency: ReportScheduleFrequency = ReportScheduleFrequency.daily
    recipient_email: EmailStr
    enabled: bool = True
    preferred_time_utc: Optional[str] = Field(
        default="09:00",
        description="Run digest at this clock time in UTC (HH:MM). Null = any time (legacy interval-only).",
    )
    weekly_day_utc: Optional[int] = Field(
        default=None,
        ge=0,
        le=6,
        description="0=Monday … 6=Sunday; used when frequency is weekly.",
    )

    @field_validator("preferred_time_utc")
    @classmethod
    def validate_hhmm(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if not _HHMM.match(v):
            raise ValueError("preferred_time_utc must be HH:MM in 24h UTC")
        return v


class ReportScheduleUpdate(BaseModel):
    min_severity: Optional[Severity] = None
    frequency: Optional[ReportScheduleFrequency] = None
    recipient_email: Optional[EmailStr] = None
    enabled: Optional[bool] = None
    preferred_time_utc: Optional[str] = None
    weekly_day_utc: Optional[int] = Field(default=None, ge=0, le=6)

    @field_validator("preferred_time_utc")
    @classmethod
    def validate_hhmm(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if v == "":
            return None
        if not _HHMM.match(v):
            raise ValueError("preferred_time_utc must be HH:MM in 24h UTC")
        return v


class ReportScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    min_severity: Severity
    frequency: ReportScheduleFrequency
    recipient_email: str
    enabled: bool
    preferred_time_utc: Optional[str] = None
    weekly_day_utc: Optional[int] = None
    last_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str
