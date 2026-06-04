"""Deterministic incident report context — stats separate from AI narrative."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.enums import IncidentStatus, Severity
from app.models.incident import Incident


@dataclass
class IncidentReportContext:
    """Structured deterministic context for incident PDF reports."""

    incident_status: str
    severity_breakdown: dict[str, int]
    mtta_seconds: float | None
    mttr_seconds: float | None
    affected_source_ips: list[str]
    affected_destinations: list[str]
    attack_timeline: list[dict[str, str]]
    correlation_summary: dict[str, Any]
    remediation_progress: str
    event_count: int
    first_event_at: str | None
    last_event_at: str | None


def _severity_key(sev: Severity | str | None) -> str:
    if sev is None:
        return "unknown"
    return sev.value if isinstance(sev, Severity) else str(sev)


def _remediation_progress(status: IncidentStatus) -> str:
    mapping = {
        IncidentStatus.open: "Not started — incident is open and awaiting triage.",
        IncidentStatus.investigating: "In progress — investigation underway.",
        IncidentStatus.resolved: "Complete — incident marked resolved.",
        IncidentStatus.false_positive: "Closed — classified as false positive.",
    }
    return mapping.get(status, "Unknown status.")


def build_incident_report_context(
    db: Session,
    incident: Incident,
    *,
    alerts: list[Alert] | None = None,
) -> IncidentReportContext:
    """Build deterministic report context from incident, events, and alerts."""
    events = list(incident.events or [])
    if alerts is None:
        alerts = list(
            db.scalars(select(Alert).where(Alert.incident_id == incident.id)).all()
        )

    severity_breakdown = Counter(_severity_key(e.severity) for e in events)
    source_ips = sorted({e.source_ip for e in events if e.source_ip})
    destinations = sorted({e.destination_ip for e in events if e.destination_ip})

    timestamps = [e.timestamp for e in events if e.timestamp]
    first_ts = min(timestamps) if timestamps else None
    last_ts = max(timestamps) if timestamps else None

    mtta_seconds: float | None = None
    if first_ts and incident.created_at:
        mtta_seconds = max((incident.created_at - first_ts).total_seconds(), 0.0)

    mttr_seconds: float | None = None
    if incident.resolved_at and incident.created_at:
        mttr_seconds = max((incident.resolved_at - incident.created_at).total_seconds(), 0.0)

    timeline: list[dict[str, str]] = []
    if first_ts:
        timeline.append(
            {
                "phase": "first_observed",
                "timestamp": first_ts.isoformat(),
                "detail": f"First linked event ({events[0].event_type if events else 'unknown'})",
            }
        )
    type_counts = Counter(e.event_type for e in events)
    for event_type, count in type_counts.most_common(5):
        timeline.append(
            {
                "phase": event_type,
                "timestamp": last_ts.isoformat() if last_ts else "",
                "detail": f"{count} event(s) of type {event_type}",
            }
        )
    if last_ts and first_ts and last_ts != first_ts:
        timeline.append(
            {
                "phase": "last_observed",
                "timestamp": last_ts.isoformat(),
                "detail": "Most recent linked telemetry",
            }
        )

    rule_families = sorted({a.rule_name for a in alerts if a.rule_name})
    # Linked incident events are authoritative; alert.event_count can be inflated when
    # multiple rules fire on the same telemetry in one evaluation pass.
    total_correlated_events = len(events) if events else sum(a.event_count or 1 for a in alerts)
    correlation_summary = {
        "alert_count": len(alerts),
        "correlated_event_count": total_correlated_events,
        "rule_families": rule_families,
        "attack_types": sorted({a.attack_type for a in alerts if a.attack_type}),
    }

    return IncidentReportContext(
        incident_status=incident.status.value.replace("_", " "),
        severity_breakdown=dict(severity_breakdown),
        mtta_seconds=mtta_seconds,
        mttr_seconds=mttr_seconds,
        affected_source_ips=source_ips,
        affected_destinations=destinations,
        attack_timeline=timeline,
        correlation_summary=correlation_summary,
        remediation_progress=_remediation_progress(incident.status),
        event_count=len(events),
        first_event_at=first_ts.isoformat() if first_ts else None,
        last_event_at=last_ts.isoformat() if last_ts else None,
    )


def format_duration(seconds: float | None) -> str:
    """Format seconds as a human-readable duration."""
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}m"
    return f"{seconds / 3600:.1f}h"


def context_to_dict(ctx: IncidentReportContext) -> dict[str, Any]:
    """Serialize context for AI grounding or API use."""
    return {
        "incident_status": ctx.incident_status,
        "severity_breakdown": ctx.severity_breakdown,
        "mtta": format_duration(ctx.mtta_seconds),
        "mttr": format_duration(ctx.mttr_seconds),
        "affected_source_ips": ctx.affected_source_ips,
        "affected_destinations": ctx.affected_destinations,
        "attack_timeline": ctx.attack_timeline,
        "correlation_summary": ctx.correlation_summary,
        "remediation_progress": ctx.remediation_progress,
        "event_count": ctx.event_count,
        "first_event_at": ctx.first_event_at,
        "last_event_at": ctx.last_event_at,
    }
