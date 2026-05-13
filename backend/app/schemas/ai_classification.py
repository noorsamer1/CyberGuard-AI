from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Severity


class AIClassificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    alert_id: Optional[int] = None
    incident_id: Optional[int] = None
    provider: str
    model: str
    prompt_type: str
    attack_type: str
    confidence: float
    suggested_severity: Severity
    why_classified: str
    evidence: list[str] = Field(default_factory=list)
    mitre_tactics: list[str] = Field(default_factory=list)
    mitre_techniques: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    should_create_alert: bool
    raw_response: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


def ai_classification_to_out(item) -> AIClassificationOut | None:
    if not item:
        return None
    try:
        severity = Severity(item.suggested_severity)
    except ValueError:
        severity = Severity.low
    return AIClassificationOut(
        id=item.id,
        event_id=item.event_id,
        alert_id=item.alert_id,
        incident_id=item.incident_id,
        provider=item.provider,
        model=item.model,
        prompt_type=item.prompt_type,
        attack_type=item.attack_type,
        confidence=float(item.confidence or 0.0),
        suggested_severity=severity,
        why_classified=item.why_classified or "",
        evidence=list(item.evidence_json or []),
        mitre_tactics=list(item.mitre_tactics_json or []),
        mitre_techniques=list(item.mitre_techniques_json or []),
        recommended_actions=list(item.recommended_actions_json or []),
        should_create_alert=bool(item.should_create_alert),
        raw_response=item.raw_response,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )
