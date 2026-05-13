from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IncidentStatus, Severity
from app.schemas.alert import MitreTechniqueOut, ThreatProfileOut
from app.schemas.event import EventOut, event_to_out
from app.services.mitre_service import get_incident_threat_intel


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    summary: str = ""
    severity: Severity
    status: IncidentStatus = IncidentStatus.open
    event_ids: list[int] = Field(default_factory=list)


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    summary: Optional[str] = None
    severity: Optional[Severity] = None
    status: Optional[IncidentStatus] = None
    analyst_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None


class IncidentLinkEvents(BaseModel):
    event_ids: list[int]


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: str
    severity: Severity
    status: IncidentStatus
    ai_summary: Optional[str] = None
    remediation: Optional[str] = None
    analyst_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    updated_at: datetime
    mitre_techniques: list[MitreTechniqueOut] = Field(default_factory=list)
    threat_profiles: list[ThreatProfileOut] = Field(default_factory=list)
    events: list[EventOut] = Field(default_factory=list)


class IncidentBriefingOut(BaseModel):
    incident_id: int
    mode: str
    executive_summary: str
    business_impact: str
    technical_findings: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    mitre_highlights: list[str] = Field(default_factory=list)


def incident_to_out(inc, include_events: bool = True) -> IncidentOut:
    evs = [event_to_out(e) for e in inc.events] if include_events else []
    rule_names: list[str] = []
    if include_events:
        for ev in inc.events:
            for alert in getattr(ev, "alerts", []):
                if alert.rule_name:
                    rule_names.append(alert.rule_name)
    techniques, profiles = get_incident_threat_intel(rule_names)
    return IncidentOut(
        id=inc.id,
        title=inc.title,
        summary=inc.summary,
        severity=inc.severity,
        status=inc.status,
        ai_summary=inc.ai_summary,
        remediation=inc.remediation,
        analyst_notes=inc.analyst_notes,
        created_at=inc.created_at,
        resolved_at=inc.resolved_at,
        updated_at=inc.updated_at,
        mitre_techniques=[MitreTechniqueOut.model_validate(t.__dict__) for t in techniques],
        threat_profiles=[ThreatProfileOut.model_validate(p.__dict__) for p in profiles],
        events=evs,
    )
