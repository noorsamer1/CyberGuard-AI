from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exercise_session import ExerciseSession
from app.models.incident import Incident
from app.schemas.incident import BriefingBenchmark, IncidentBriefingOut


@dataclass(frozen=True)
class _Counts:
    events: int
    unique_sources: int
    high_or_critical: int


def build_incident_briefing(db: Session, incident: Incident, mode: str) -> IncidentBriefingOut:
    """Build a concise incident briefing for analyst or executive audiences."""
    counts = _count_incident_signals(incident)
    benchmark = _build_learning_benchmark(db, incident.owner_id)
    mitre_ids = sorted({t.technique_id for t in _get_techniques(incident)})

    executive_summary = (
        f"Incident '{incident.title}' is {incident.status.value} with {counts.events} correlated events "
        f"from {counts.unique_sources} source(s). Severity is {incident.severity.value}."
    )
    business_impact = (
        "Potential operational disruption and increased breach likelihood if containment is delayed. "
        f"{counts.high_or_critical} high/critical signal(s) were observed."
    )
    technical_findings = [
        f"Correlated events: {counts.events}",
        f"Unique source IPs: {counts.unique_sources}",
        f"High/Critical events: {counts.high_or_critical}",
    ]
    if incident.ai_summary:
        technical_findings.append(f"AI insight: {incident.ai_summary[:220]}")

    recommended_actions = [
        "Contain suspicious source endpoints and revoke risky sessions.",
        "Validate detection rule tuning to reduce repeat high-severity triggers.",
        "Document IOC timeline and confirm remediation evidence.",
    ]
    if mode == "technical":
        recommended_actions.append(
            "Cross-check firewall, IAM, and endpoint logs for lateral movement indicators."
        )

    return IncidentBriefingOut(
        incident_id=incident.id,
        mode=mode,
        executive_summary=executive_summary,
        business_impact=business_impact,
        technical_findings=technical_findings,
        recommended_actions=recommended_actions,
        mitre_highlights=mitre_ids,
        learning_benchmark=benchmark,
    )


def _count_incident_signals(incident: Incident) -> _Counts:
    events = list(incident.events or [])
    unique_sources = len({event.source_ip for event in events if event.source_ip})
    high_or_critical = sum(1 for event in events if event.severity.value in {"high", "critical"})
    return _Counts(events=len(events), unique_sources=unique_sources, high_or_critical=high_or_critical)


def _build_learning_benchmark(db: Session, owner_id: int | None) -> BriefingBenchmark:
    if owner_id is None:
        return BriefingBenchmark()

    completed = db.scalars(
        select(ExerciseSession.overall_score)
        .where(
            ExerciseSession.user_id == owner_id,
            ExerciseSession.overall_score.is_not(None),
        )
        .order_by(ExerciseSession.completed_at.desc())
        .limit(20)
    ).all()
    scores = [float(score) for score in completed if score is not None]
    if not scores:
        return BriefingBenchmark()

    average = round(float(sum(scores)) / len(scores), 2)
    latest = round(scores[0], 2)
    if len(scores) >= 3 and latest >= average:
        trend = "improving"
    elif len(scores) >= 3 and latest < average:
        trend = "declining"
    else:
        trend = "stable"
    return BriefingBenchmark(
        average_score=average,
        latest_score=latest,
        sessions_completed=len(scores),
        trend=trend,
    )


def _get_techniques(incident: Incident):
    from app.services.mitre_service import get_incident_threat_intel

    rule_names: list[str] = []
    for event in incident.events or []:
        for alert in getattr(event, "alerts", []):
            if alert.rule_name:
                rule_names.append(alert.rule_name)
    techniques, _ = get_incident_threat_intel(rule_names)
    return techniques
