"""Alert correlation helpers — group related detections into one alert/incident."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.detection.rules.base import RuleHit
from app.models.alert import Alert
from app.models.enums import AlertStatus, Severity
from app.models.event import Event
from app.models.incident import Incident

_SEVERITY_ORDER = [Severity.low, Severity.medium, Severity.high, Severity.critical]


def build_correlation_key(attack_type: str, event: Event) -> str:
    """Build a stable correlation key from attack type, source, and target."""
    source = event.source_ip or "na"
    target = event.destination_ip or (str(event.port) if event.port is not None else "na")
    return f"{attack_type}:{source}:{target}"


def max_severity(current: Severity, candidate: Severity) -> Severity:
    """Return the higher of two severities."""
    if _SEVERITY_ORDER.index(candidate) > _SEVERITY_ORDER.index(current):
        return candidate
    return current


def find_correlated_alert(
    db: Session,
    *,
    owner_id: int | None,
    correlation_key: str,
    event_timestamp: datetime,
) -> Alert | None:
    """Find an open correlated alert within the configured time window."""
    window = timedelta(minutes=max(settings.correlation_window_minutes, 1))
    window_start = event_timestamp - window
    stmt = (
        select(Alert)
        .where(
            and_(
                Alert.correlation_key == correlation_key,
                Alert.owner_id == owner_id,
                Alert.status.in_([AlertStatus.new, AlertStatus.acknowledged]),
                Alert.last_seen_at >= window_start,
                Alert.last_seen_at <= event_timestamp,
            )
        )
        .order_by(Alert.last_seen_at.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def attach_event_to_correlated_alert(
    db: Session,
    alert: Alert,
    event: Event,
    hit: RuleHit,
) -> None:
    """Append an event to an existing correlated alert/incident."""
    already_linked = False
    incident: Incident | None = None
    if alert.incident_id:
        incident = db.get(Incident, alert.incident_id)
        if incident and event.id and event in incident.events:
            already_linked = True

    if not already_linked:
        alert.event_count = (alert.event_count or 1) + 1

    alert.last_seen_at = event.timestamp
    alert.severity = max_severity(alert.severity, hit.severity)
    if hit.description and alert.description:
        if hit.description not in alert.description:
            alert.description = f"{alert.description} | {hit.description}"
    elif hit.description:
        alert.description = hit.description
    db.add(alert)

    if incident and event.id and not already_linked:
        incident.events.append(event)
        incident.severity = max_severity(incident.severity, hit.severity)
        db.add(incident)
