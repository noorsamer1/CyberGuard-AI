from typing import Any

from pydantic import BaseModel

from app.models.enums import Severity


class DashboardSummary(BaseModel):
    events_today: int
    suspicious_events: int
    dangerous_events: int
    active_incidents: int
    resolved_incidents: int
    open_alerts: int
    mtta_minutes: float
    mttr_minutes: float
    new_alerts_24h: int
    unassigned_open_incidents: int
    critical_open_incidents: int
    event_to_alert_conversion_pct: float
    mitre_coverage_count: int
    security_overview: str | None = None


class SeverityCount(BaseModel):
    severity: Severity
    count: int


class TimeSeriesPoint(BaseModel):
    bucket: str
    count: int


class TimelinePoint(BaseModel):
    bucket: str
    events: int
    alerts: int
    incidents: int


class WorkQueueBuckets(BaseModel):
    alerts_new: int
    alerts_acknowledged: int
    alerts_resolved: int
    incidents_open: int
    incidents_investigating: int
    incidents_resolved: int
    incidents_overdue: int


class RuleCount(BaseModel):
    rule_name: str
    count: int


class SourceRiskPoint(BaseModel):
    source_ip: str
    high_critical_events: int
    alerts: int


class MitreCoveragePoint(BaseModel):
    technique_id: str
    count: int


class AnomalySignals(BaseModel):
    exfiltration_alerts: int
    auth_anomaly_alerts: int
    outbound_transfer_events: int
    privileged_login_events: int


class DashboardCharts(BaseModel):
    severity_distribution: list[SeverityCount]
    events_timeline: list[TimeSeriesPoint]
    top_event_types: list[dict[str, Any]]
    source_ip_activity: list[dict[str, Any]]
    attack_timeline: list[TimelinePoint]
    work_queue: WorkQueueBuckets
    top_rules_24h: list[RuleCount]
    top_risks: list[SourceRiskPoint]
    mitre_coverage: list[MitreCoveragePoint]
    anomaly_signals: AnomalySignals


class UIRecommendation(BaseModel):
    id: str
    title: str
    rationale: str
    action_label: str
    action_href: str
    severity: str
