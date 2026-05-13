"""Request/response models for incident portfolio AI reports."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.enums import IncidentStatus, Severity


class PortfolioReportRequest(BaseModel):
    """Filters aligned with GET /incidents list."""

    status: Optional[IncidentStatus] = None
    severity: Optional[Severity] = None
    q: Optional[str] = Field(default=None, max_length=512)
    max_items: int = Field(default=150, ge=1, le=500)


class PortfolioAIOut(BaseModel):
    """Structured LLM output; must not invent counts beyond provided stats."""

    executive_summary: str = ""
    key_findings: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)


class IncidentPortfolioReportOut(BaseModel):
    """Full portfolio report payload for the frontend (charts + AI narrative)."""

    generated_at: str
    filters: dict[str, Any]
    max_items: int
    truncated: bool
    truncation_note: Optional[str] = None
    stats: dict[str, Any]
    charts: dict[str, Any]
    ai: Optional[PortfolioAIOut] = None
    ai_error: Optional[str] = None
