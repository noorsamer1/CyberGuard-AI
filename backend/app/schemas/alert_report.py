"""Request models for alert portfolio PDF generation."""

from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import AlertStatus, Severity


class AlertPortfolioReportRequest(BaseModel):
    """Filters applied when building the alert portfolio PDF."""

    severity: Optional[Severity] = None
    status: Optional[AlertStatus] = None
    max_alerts: int = Field(default=500, ge=1, le=1000)
