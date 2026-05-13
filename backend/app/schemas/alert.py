from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AlertStatus, Severity
from app.schemas.ai_classification import AIClassificationOut, ai_classification_to_out
from app.services.mitre_service import get_alert_threat_intel


class MitreTechniqueOut(BaseModel):
    tactic: str
    technique: str
    technique_id: str
    sub_technique: str | None = None


class ThreatProfileOut(BaseModel):
    actor: str
    confidence: str
    cve_references: list[str]
    kill_chain_phase: str


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    severity: Severity
    rule_name: str
    status: AlertStatus
    reasoning: Optional[str] = None
    ai_assessment: Optional[AIClassificationOut] = None
    mitre_techniques: list[MitreTechniqueOut] = Field(default_factory=list)
    threat_profile: ThreatProfileOut | None = None
    created_at: datetime
    updated_at: datetime


class AlertStatusUpdate(BaseModel):
    status: AlertStatus


def alert_to_out(a) -> AlertOut:
    techniques, profile = get_alert_threat_intel(a.rule_name)
    ai_assessment = None
    if getattr(a, "ai_classifications", None):
        ai_assessment = ai_classification_to_out(a.ai_classifications[0])
    if ai_assessment is None and getattr(a, "event", None):
        ai_assessment = ai_classification_to_out(getattr(a.event, "ai_classification", None))
    return AlertOut(
        id=a.id,
        event_id=a.event_id,
        title=a.title,
        description=a.description,
        severity=a.severity,
        rule_name=a.rule_name,
        status=a.status,
        reasoning=a.reasoning,
        ai_assessment=ai_assessment,
        mitre_techniques=[MitreTechniqueOut.model_validate(t.__dict__) for t in techniques],
        threat_profile=ThreatProfileOut.model_validate(profile.__dict__) if profile else None,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )
