from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.logging import get_logger
from app.models.ai_classification import AIClassification
from app.models.alert import Alert
from app.models.enums import AlertStatus, IncidentStatus, Severity
from app.models.event import Event
from app.models.incident import Incident, incident_events
from app.services import ai_service

logger = get_logger(__name__)

SUSPICIOUS_ATTACK_TYPES = {
    "brute_force",
    "sql_injection",
    "path_traversal",
    "port_scan",
    "data_exfiltration",
    "ransomware",
    "suspicious_upload",
    "denied_access_spike",
    "rate_anomaly",
    "lateral_movement",
}


def classify_events(db: Session, event_ids: list[int]) -> int:
    if not settings.ai_detection_enabled:
        return 0
    if not settings.openrouter_api_key:
        logger.info("AI detection enabled but OpenRouter API key is not configured")
        return 0

    max_items = max(int(settings.ai_detection_max_events_per_task or 1), 1)
    ids = [int(eid) for eid in event_ids[:max_items] if eid]
    if not ids:
        return 0

    rows = list(
        db.scalars(
            select(Event)
            .options(selectinload(Event.alerts), selectinload(Event.ai_classification))
            .where(Event.id.in_(ids))
        ).all()
    )
    created = 0
    for event in rows:
        if event.ai_classification:
            continue
        try:
            result = ai_service.classify_event_context(_event_context(event))
            if not result:
                continue
            _store_classification(db, event, result)
            db.commit()
            created += 1
        except Exception:
            db.rollback()
            logger.warning("Failed to store AI classification for event_id=%s", event.id, exc_info=True)
    return created


def get_event_classification(db: Session, event_id: int, owner_id: int | None = None) -> AIClassification | None:
    conds = [AIClassification.event_id == event_id]
    if owner_id is not None:
        conds.append(AIClassification.owner_id == owner_id)
    return db.scalars(select(AIClassification).where(*conds)).first()


def get_alert_classification(db: Session, alert: Alert, owner_id: int | None = None) -> AIClassification | None:
    conds = []
    if owner_id is not None:
        conds.append(AIClassification.owner_id == owner_id)
    direct = db.scalars(select(AIClassification).where(AIClassification.alert_id == alert.id, *conds)).first()
    if direct:
        return direct
    if alert.event_id is None:
        return None
    return get_event_classification(db, alert.event_id, owner_id=owner_id)


def _store_classification(db: Session, event: Event, result: dict[str, Any]) -> AIClassification:
    existing_alert = event.alerts[0] if event.alerts else None
    incident_id = _first_incident_id_for_event(db, event.id)
    grounded = _has_grounded_evidence(event, result.get("evidence") or [])
    should_create_ai_alert = _should_create_ai_alert(result, grounded, existing_alert is not None)

    classification = AIClassification(
        event_id=event.id,
        alert_id=existing_alert.id if existing_alert else None,
        incident_id=incident_id,
        owner_id=event.owner_id,
        provider="openrouter",
        model=settings.openrouter_model,
        prompt_type="event_classify",
        attack_type=result["attack_type"],
        confidence=result["confidence"],
        suggested_severity=result["suggested_severity"],
        why_classified=result["why_classified"],
        evidence_json=result["evidence"],
        mitre_tactics_json=result["mitre_tactics"],
        mitre_techniques_json=result["mitre_techniques"],
        recommended_actions_json=result["recommended_actions"],
        should_create_alert=should_create_ai_alert,
        raw_response=result.get("raw_response") or result,
    )
    db.add(classification)
    db.flush()

    if should_create_ai_alert:
        alert, incident = _create_ai_alert_and_incident(db, event, result)
        classification.alert_id = alert.id
        classification.incident_id = incident.id
        classification.updated_at = datetime.now(timezone.utc)
        db.flush()
    return classification


def _should_create_ai_alert(result: dict[str, Any], grounded: bool, has_rule_alert: bool) -> bool:
    if has_rule_alert:
        return False
    if result["attack_type"] not in SUSPICIOUS_ATTACK_TYPES:
        return False
    if result["confidence"] < settings.ai_detection_min_confidence:
        return False
    if not result.get("should_create_alert"):
        return False
    if not grounded:
        return False
    return True


def _create_ai_alert_and_incident(db: Session, event: Event, result: dict[str, Any]) -> tuple[Alert, Incident]:
    title = f"AI classified {result['attack_type'].replace('_', ' ')} activity"
    description = result.get("why_classified") or title
    severity = _severity(result.get("suggested_severity"))
    evidence = result.get("evidence") or []
    reasoning = (
        f"AI confidence: {result['confidence']:.2f}. "
        f"Evidence: {', '.join(evidence[:4]) if evidence else 'No evidence provided'}"
    )
    alert = Alert(
        event_id=event.id,
        title=title,
        description=description,
        severity=severity,
        rule_name="ai_classifier",
        status=AlertStatus.new,
        reasoning=reasoning,
        owner_id=event.owner_id,
    )
    db.add(alert)
    db.flush()
    incident = Incident(
        title=title,
        summary=description,
        severity=severity,
        status=IncidentStatus.open,
        owner_id=event.owner_id,
    )
    db.add(incident)
    db.flush()
    incident.events.append(event)
    db.flush()
    return alert, incident


def _first_incident_id_for_event(db: Session, event_id: int | None) -> int | None:
    if not event_id:
        return None
    return db.scalar(select(incident_events.c.incident_id).where(incident_events.c.event_id == event_id).limit(1))


def _severity(value: str | None) -> Severity:
    try:
        return Severity(value or "low")
    except ValueError:
        return Severity.low


def _event_context(event: Event) -> dict[str, Any]:
    return {
        "id": event.id,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "source_ip": event.source_ip,
        "destination_ip": event.destination_ip,
        "username": event.username,
        "event_type": event.event_type,
        "status": event.status,
        "severity_hint": event.severity.value if event.severity else None,
        "message": (event.message or "")[:1200],
        "protocol": event.protocol,
        "port": event.port,
        "source_system": event.source_system,
        "raw_log": (event.raw_log or "")[:1800],
        "metadata": event.metadata_json or {},
    }


def _has_grounded_evidence(event: Event, evidence: list[str]) -> bool:
    if not evidence:
        return False
    chunks = [
        event.source_ip,
        event.destination_ip,
        event.username,
        event.event_type,
        event.status,
        event.message,
        event.protocol,
        str(event.port) if event.port is not None else None,
        event.raw_log,
        event.source_system,
        json.dumps(event.metadata_json or {}, default=str),
    ]
    haystack = "\n".join(c for c in chunks if c).lower()
    for item in evidence:
        needle = str(item).strip().lower()
        if needle and (needle in haystack or any(part and part in haystack for part in needle.split() if len(part) >= 5)):
            return True
    return False


def request_ai_classification_for_alert(
    db: Session,
    *,
    alert: Alert,
    owner_id: int,
) -> tuple[AIClassification | None, str]:
    """Return AI classification for an alert, running the LLM once if missing.

    The alert's rule-based severity is unchanged; this only creates advisory
    ``AIClassification`` rows when enabled.

    Args:
        db: Database session.
        alert: Alert row (caller must enforce tenant ownership).
        owner_id: Expected alert/event owner.

    Returns:
        ``(classification, "")`` on success, or ``(None, error_code)`` where
        ``error_code`` is one of: ``not_owner``, ``no_event``, ``ai_disabled``,
        ``no_api_key``, ``classification_unavailable``.
    """
    if alert.owner_id != owner_id:
        return None, "not_owner"

    existing = get_alert_classification(db, alert, owner_id=owner_id)
    if existing:
        return existing, ""

    if not alert.event_id:
        return None, "no_event"

    event = db.get(Event, alert.event_id)
    if event is None or event.owner_id != owner_id:
        return None, "no_event"

    if not settings.ai_detection_enabled:
        return None, "ai_disabled"

    if not settings.openrouter_api_key:
        return None, "no_api_key"

    classify_events(db, [int(alert.event_id)])
    item = get_alert_classification(db, alert, owner_id=owner_id)
    if item:
        return item, ""
    return None, "classification_unavailable"
