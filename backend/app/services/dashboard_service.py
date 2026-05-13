from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.enums import AlertStatus, IncidentStatus, Severity
from app.models.event import Event
from app.models.incident import Incident
from app.schemas.dashboard import (
    AnomalySignals,
    DashboardCharts,
    DashboardSummary,
    MitreCoveragePoint,
    RuleCount,
    SeverityCount,
    SourceRiskPoint,
    TimelinePoint,
    TimeSeriesPoint,
    UIRecommendation,
    WorkQueueBuckets,
)
from app.services.mitre_service import get_alert_threat_intel


def _start_of_today_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _window_start(window: str) -> datetime:
    now = datetime.now(timezone.utc)
    if window == "24h":
        return now - timedelta(hours=24)
    if window == "30d":
        return now - timedelta(days=30)
    return now - timedelta(days=7)


def _average_minutes(durations: list[float]) -> float:
    if not durations:
        return 0.0
    return round(sum(durations) / len(durations), 2)


def get_summary(db: Session, owner_id: int | None = None, window: str = "24h") -> DashboardSummary:
    start = _start_of_today_utc()
    recent_start = _window_start(window)
    event_filters = [Event.timestamp >= start]
    if owner_id is not None:
        event_filters.append(Event.owner_id == owner_id)
    events_today = db.scalar(select(func.count()).select_from(Event).where(*event_filters)) or 0
    suspicious = (
        db.scalar(
            select(func.count())
            .select_from(Event)
            .where(*event_filters, Event.severity == Severity.medium)
        )
        or 0
    )
    dangerous = (
        db.scalar(
            select(func.count())
            .select_from(Event)
            .where(
                *event_filters,
                Event.severity.in_([Severity.high, Severity.critical]),
            )
        )
        or 0
    )
    incident_filters = []
    if owner_id is not None:
        incident_filters.append(Incident.owner_id == owner_id)
    active_inc = (
        db.scalar(
            select(func.count())
            .select_from(Incident)
            .where(*incident_filters, Incident.status.in_([IncidentStatus.open, IncidentStatus.investigating]))
        )
        or 0
    )
    resolved_inc = (
        db.scalar(
            select(func.count()).select_from(Incident).where(*incident_filters, Incident.status == IncidentStatus.resolved)
        )
        or 0
    )
    alert_filters = [Alert.status == AlertStatus.new]
    if owner_id is not None:
        alert_filters.append(Alert.owner_id == owner_id)
    open_alerts = (
        db.scalar(
            select(func.count()).select_from(Alert).where(*alert_filters)
        )
        or 0
    )
    recent_alert_filters = [Alert.created_at >= recent_start]
    if owner_id is not None:
        recent_alert_filters.append(Alert.owner_id == owner_id)
    new_alerts_24h = (
        db.scalar(
            select(func.count())
            .select_from(Alert)
            .where(*recent_alert_filters, Alert.status == AlertStatus.new)
        )
        or 0
    )
    unresolved_incident_statuses = [IncidentStatus.open, IncidentStatus.investigating]
    unresolved_incident_filters = [Incident.status.in_(unresolved_incident_statuses)]
    if owner_id is not None:
        unresolved_incident_filters.append(Incident.owner_id == owner_id)
    unassigned_open_incidents = (
        db.scalar(select(func.count()).select_from(Incident).where(*unresolved_incident_filters)) or 0
    )
    critical_open_incidents = (
        db.scalar(
            select(func.count())
            .select_from(Incident)
            .where(*unresolved_incident_filters, Incident.severity == Severity.critical)
        )
        or 0
    )
    recent_event_filters = [Event.timestamp >= recent_start]
    if owner_id is not None:
        recent_event_filters.append(Event.owner_id == owner_id)
    recent_events = db.scalar(select(func.count()).select_from(Event).where(*recent_event_filters)) or 0
    recent_alerts = db.scalar(select(func.count()).select_from(Alert).where(*recent_alert_filters)) or 0
    event_to_alert_conversion_pct = round(((recent_alerts / recent_events) * 100), 2) if recent_events else 0.0

    # MTTA approximated as avg minutes between alert create and first triage state update.
    triaged_alerts = db.scalars(
        select(Alert).where(
            *recent_alert_filters, Alert.status.in_([AlertStatus.acknowledged, AlertStatus.resolved])
        )
    ).all()
    mtta_durations = [
        max((alert.updated_at - alert.created_at).total_seconds() / 60.0, 0.0) for alert in triaged_alerts
    ]
    mtta_minutes = _average_minutes(mtta_durations)

    # MTTR as avg minutes between incident create and resolved_at for resolved incidents.
    incident_recent_filters = [Incident.created_at >= recent_start]
    if owner_id is not None:
        incident_recent_filters.append(Incident.owner_id == owner_id)
    resolved_incidents_rows = db.scalars(
        select(Incident).where(
            *incident_recent_filters,
            Incident.status == IncidentStatus.resolved,
            Incident.resolved_at.is_not(None),
        )
    ).all()
    mttr_durations = [
        max((incident.resolved_at - incident.created_at).total_seconds() / 60.0, 0.0)
        for incident in resolved_incidents_rows
        if incident.resolved_at is not None
    ]
    mttr_minutes = _average_minutes(mttr_durations)

    mitre_rules = db.scalars(
        select(Alert.rule_name).where(*recent_alert_filters)
    ).all()
    technique_ids: set[str] = set()
    for rule_name in mitre_rules:
        techniques, _ = get_alert_threat_intel(rule_name)
        for technique in techniques:
            technique_ids.add(technique.technique_id)
    mitre_coverage_count = len(technique_ids)
    overview_parts = [
        f"Today's ingest: {events_today} events.",
        f"Elevated activity: {suspicious} suspicious and {dangerous} high-severity events.",
        f"Incidents: {active_inc} active, {resolved_inc} resolved.",
        f"Open alerts awaiting triage: {open_alerts}.",
    ]
    return DashboardSummary(
        events_today=events_today,
        suspicious_events=suspicious,
        dangerous_events=dangerous,
        active_incidents=active_inc,
        resolved_incidents=resolved_inc,
        open_alerts=open_alerts,
        mtta_minutes=mtta_minutes,
        mttr_minutes=mttr_minutes,
        new_alerts_24h=new_alerts_24h,
        unassigned_open_incidents=unassigned_open_incidents,
        critical_open_incidents=critical_open_incidents,
        event_to_alert_conversion_pct=event_to_alert_conversion_pct,
        mitre_coverage_count=mitre_coverage_count,
        security_overview=" ".join(overview_parts),
    )


def get_charts(db: Session, owner_id: int | None = None, window: str = "24h") -> DashboardCharts:
    start = _window_start(window)
    event_filters = [Event.timestamp >= start]
    if owner_id is not None:
        event_filters.append(Event.owner_id == owner_id)
    sev_rows = db.execute(
        select(Event.severity, func.count())
        .where(*event_filters)
        .group_by(Event.severity)
    ).all()
    severity_distribution = [
        SeverityCount(severity=row[0], count=int(row[1])) for row in sev_rows
    ]
    timeline_rows = db.execute(
        select(
            func.date_trunc("day", Event.timestamp).label("bucket"),
            func.count(),
        )
        .where(*event_filters)
        .group_by("bucket")
        .order_by("bucket")
    ).all()
    events_timeline = [
        TimeSeriesPoint(bucket=str(row[0].date()) if row[0] else "", count=int(row[1]))
        for row in timeline_rows
    ]
    type_rows = db.execute(
        select(Event.event_type, func.count())
        .where(*event_filters)
        .group_by(Event.event_type)
        .order_by(func.count().desc())
        .limit(8)
    ).all()
    top_event_types = [{"event_type": r[0], "count": int(r[1])} for r in type_rows]
    ip_rows = db.execute(
        select(Event.source_ip, func.count())
        .where(*event_filters, Event.source_ip.isnot(None))
        .group_by(Event.source_ip)
        .order_by(func.count().desc())
        .limit(10)
    ).all()
    source_ip_activity = [{"source_ip": r[0], "count": int(r[1])} for r in ip_rows]

    alert_filters = [Alert.created_at >= start]
    incident_filters = [Incident.created_at >= start]
    if owner_id is not None:
        alert_filters.append(Alert.owner_id == owner_id)
        incident_filters.append(Incident.owner_id == owner_id)
    time_bucket = "hour" if window == "24h" else "day"

    event_timeline_rows = db.execute(
        select(func.date_trunc(time_bucket, Event.timestamp).label("bucket"), func.count())
        .where(*event_filters)
        .group_by("bucket")
    ).all()
    alert_timeline_rows = db.execute(
        select(func.date_trunc(time_bucket, Alert.created_at).label("bucket"), func.count())
        .where(*alert_filters)
        .group_by("bucket")
    ).all()
    incident_timeline_rows = db.execute(
        select(func.date_trunc(time_bucket, Incident.created_at).label("bucket"), func.count())
        .where(*incident_filters)
        .group_by("bucket")
    ).all()
    events_map = {row[0]: int(row[1]) for row in event_timeline_rows}
    alerts_map = {row[0]: int(row[1]) for row in alert_timeline_rows}
    incidents_map = {row[0]: int(row[1]) for row in incident_timeline_rows}
    all_buckets = sorted(set(events_map) | set(alerts_map) | set(incidents_map))
    attack_timeline = [
        TimelinePoint(
            bucket=str(bucket.isoformat() if bucket else ""),
            events=events_map.get(bucket, 0),
            alerts=alerts_map.get(bucket, 0),
            incidents=incidents_map.get(bucket, 0),
        )
        for bucket in all_buckets
    ]

    alerts_new = db.scalar(
        select(func.count()).select_from(Alert).where(*alert_filters, Alert.status == AlertStatus.new)
    ) or 0
    alerts_ack = db.scalar(
        select(func.count()).select_from(Alert).where(*alert_filters, Alert.status == AlertStatus.acknowledged)
    ) or 0
    alerts_resolved = db.scalar(
        select(func.count()).select_from(Alert).where(*alert_filters, Alert.status == AlertStatus.resolved)
    ) or 0
    incidents_open = db.scalar(
        select(func.count()).select_from(Incident).where(*incident_filters, Incident.status == IncidentStatus.open)
    ) or 0
    incidents_investigating = db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(*incident_filters, Incident.status == IncidentStatus.investigating)
    ) or 0
    incidents_resolved = db.scalar(
        select(func.count()).select_from(Incident).where(*incident_filters, Incident.status == IncidentStatus.resolved)
    ) or 0
    overdue_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    incidents_overdue = db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(
            *incident_filters,
            Incident.status.in_([IncidentStatus.open, IncidentStatus.investigating]),
            Incident.created_at < overdue_cutoff,
        )
    ) or 0
    work_queue = WorkQueueBuckets(
        alerts_new=alerts_new,
        alerts_acknowledged=alerts_ack,
        alerts_resolved=alerts_resolved,
        incidents_open=incidents_open,
        incidents_investigating=incidents_investigating,
        incidents_resolved=incidents_resolved,
        incidents_overdue=incidents_overdue,
    )

    top_rule_rows = db.execute(
        select(Alert.rule_name, func.count())
        .where(*alert_filters)
        .group_by(Alert.rule_name)
        .order_by(func.count().desc())
        .limit(8)
    ).all()
    top_rules_24h = [RuleCount(rule_name=row[0], count=int(row[1])) for row in top_rule_rows]

    risk_rows = db.execute(
        select(Event.source_ip, func.count())
        .where(
            *event_filters,
            Event.source_ip.is_not(None),
            Event.severity.in_([Severity.medium, Severity.high, Severity.critical]),
        )
        .group_by(Event.source_ip)
        .order_by(func.count().desc())
        .limit(8)
    ).all()
    top_risks: list[SourceRiskPoint] = []
    for source_ip, hc_count in risk_rows:
        alerts_for_ip = db.scalar(
            select(func.count())
            .select_from(Alert)
            .join(Event, Alert.event_id == Event.id, isouter=True)
            .where(*alert_filters, Event.source_ip == source_ip)
        ) or 0
        top_risks.append(
            SourceRiskPoint(
                source_ip=str(source_ip),
                high_critical_events=int(hc_count),
                alerts=int(alerts_for_ip),
            )
        )

    mitre_counter: dict[str, int] = {}
    for rule_name, count in top_rule_rows:
        techniques, _ = get_alert_threat_intel(rule_name)
        for technique in techniques:
            mitre_counter[technique.technique_id] = mitre_counter.get(technique.technique_id, 0) + int(count)
    mitre_coverage = [
        MitreCoveragePoint(technique_id=technique_id, count=count)
        for technique_id, count in sorted(mitre_counter.items(), key=lambda item: item[1], reverse=True)
    ]

    exfiltration_alerts = db.scalar(
        select(func.count()).select_from(Alert).where(*alert_filters, Alert.rule_name == "data_exfiltration")
    ) or 0
    auth_anomaly_alerts = db.scalar(
        select(func.count())
        .select_from(Alert)
        .where(*alert_filters, Alert.rule_name.in_(["brute_force", "failed_login_burst"]))
    ) or 0
    outbound_transfer_events = db.scalar(
        select(func.count())
        .select_from(Event)
        .where(*event_filters, Event.message.ilike("%outbound data transfer%"))
    ) or 0
    privileged_login_events = db.scalar(
        select(func.count())
        .select_from(Event)
        .where(
            *event_filters,
            Event.event_type == "authentication",
            Event.message.ilike("%privileged%"),
        )
    ) or 0
    anomaly_signals = AnomalySignals(
        exfiltration_alerts=exfiltration_alerts,
        auth_anomaly_alerts=auth_anomaly_alerts,
        outbound_transfer_events=outbound_transfer_events,
        privileged_login_events=privileged_login_events,
    )

    return DashboardCharts(
        severity_distribution=severity_distribution,
        events_timeline=events_timeline,
        top_event_types=top_event_types,
        source_ip_activity=source_ip_activity,
        attack_timeline=attack_timeline,
        work_queue=work_queue,
        top_rules_24h=top_rules_24h,
        top_risks=top_risks,
        mitre_coverage=mitre_coverage,
        anomaly_signals=anomaly_signals,
    )


def recent_incidents_table(
    db: Session, limit: int = 8, owner_id: int | None = None
) -> list[dict[str, Any]]:
    stmt = select(Incident)
    if owner_id is not None:
        stmt = stmt.where(Incident.owner_id == owner_id)
    rows = db.scalars(
        stmt.order_by(Incident.created_at.desc()).limit(limit)
    ).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "severity": r.severity.value,
            "status": r.status.value,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


def recent_alerts_table(
    db: Session, limit: int = 10, owner_id: int | None = None
) -> list[dict[str, Any]]:
    stmt = select(Alert)
    if owner_id is not None:
        stmt = stmt.where(Alert.owner_id == owner_id)
    rows = db.scalars(stmt.order_by(Alert.created_at.desc()).limit(limit)).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "severity": r.severity.value,
            "rule_name": r.rule_name,
            "status": r.status.value,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


def get_ui_recommendations(db: Session, owner_id: int) -> list[UIRecommendation]:
    """Return action-oriented UX recommendations based on current SOC state."""
    open_alerts = db.scalar(
        select(func.count()).select_from(Alert).where(
            Alert.owner_id == owner_id,
            Alert.status == AlertStatus.new,
        )
    ) or 0
    active_incidents = db.scalar(
        select(func.count()).select_from(Incident).where(
            Incident.owner_id == owner_id,
            Incident.status.in_([IncidentStatus.open, IncidentStatus.investigating]),
        )
    ) or 0
    recommendations: list[UIRecommendation] = []

    if open_alerts >= 10:
        recommendations.append(
            UIRecommendation(
                id="triage-overload",
                title="Triage overload detected",
                rationale="High queue depth can hide critical alerts.",
                action_label="Open Alerts Queue",
                action_href="/alerts",
                severity="high",
            )
        )
    if active_incidents == 0:
        recommendations.append(
            UIRecommendation(
                id="empty-incident-flow",
                title="No active incidents",
                rationale="Run a scenario to keep analysts calibrated with realistic pressure.",
                action_label="Launch Attack Lab",
                action_href="/attack-lab",
                severity="medium",
            )
        )
    if not recommendations:
        recommendations.append(
            UIRecommendation(
                id="healthy-posture",
                title="Operational posture is healthy",
                rationale="Current queue and workflow are within expected limits.",
                action_label="Review Dashboard",
                action_href="/dashboard",
                severity="info",
            )
        )
    # Learning / exercise flows were removed; never surface stale advisor rows.
    drop_ids = frozenset({"training-cadence", "learning-session", "low-training-cadence"})
    return [
        r
        for r in recommendations
        if r.id not in drop_ids
        and "/learning" not in r.action_href.lower()
        and "/exercise" not in r.action_href.lower()
    ]
