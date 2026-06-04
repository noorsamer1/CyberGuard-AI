from sqlalchemy.orm import Session

from app.core.config import settings
from app.detection.correlation import (
    attach_event_to_correlated_alert,
    build_correlation_key,
    find_correlated_alert,
)
from app.detection.rules.base import DetectionRule, RuleHit
from app.detection.rules.brute_force_rule import BruteForceRule
from app.detection.rules.command_injection_rule import CommandInjectionRule
from app.detection.rules.data_exfiltration_rule import DataExfiltrationRule
from app.detection.rules.denied_spike_rule import DeniedSpikeRule
from app.detection.rules.dns_tunneling_rule import DnsTunnelingRule
from app.detection.rules.failed_login_rule import FailedLoginBurstRule
from app.detection.rules.path_traversal_rule import PathTraversalRule
from app.detection.rules.password_spray_rule import PasswordSprayRule
from app.detection.rules.port_scan_rule import PortScanRule
from app.detection.rules.privilege_escalation_rule import PrivilegeEscalationRule
from app.detection.rules.ransomware_simulation_rule import RansomwareSimulationRule
from app.detection.rules.rate_anomaly_rule import RateAnomalyRule
from app.detection.rules.sql_injection_rule import SqlInjectionRule
from app.detection.rules.suspicious_upload_rule import SuspiciousUploadRule
from app.models.alert import Alert
from app.models.enums import AlertStatus, IncidentStatus
from app.models.event import Event
from app.models.incident import Incident


class DetectionEngine:
    def __init__(self) -> None:
        self.rules: list[DetectionRule] = [
            RateAnomalyRule(),
            PortScanRule(),
            BruteForceRule(),
            FailedLoginBurstRule(),
            DeniedSpikeRule(),
            DataExfiltrationRule(),
            SqlInjectionRule(),
            PathTraversalRule(),
            SuspiciousUploadRule(),
            RansomwareSimulationRule(),
            DnsTunnelingRule(),
            PasswordSprayRule(),
            CommandInjectionRule(),
            PrivilegeEscalationRule(),
        ]

    def run(self, db: Session, event: Event) -> list[Alert]:
        hits: list[RuleHit] = []
        for rule in self.rules:
            hits.extend(rule.evaluate(db, event))

        alerts: list[Alert] = []
        session_keys: dict[str, Alert] = {}

        for hit in hits:
            correlation_key: str | None = None
            if settings.correlation_enabled:
                correlation_key = build_correlation_key(hit.attack_type, event)
                if correlation_key in session_keys:
                    attach_event_to_correlated_alert(db, session_keys[correlation_key], event, hit)
                    continue
                existing = find_correlated_alert(
                    db,
                    owner_id=event.owner_id,
                    correlation_key=correlation_key,
                    event_timestamp=event.timestamp,
                )
                if existing:
                    attach_event_to_correlated_alert(db, existing, event, hit)
                    session_keys[correlation_key] = existing
                    continue

            alert = Alert(
                event_id=hit.event_id,
                title=hit.title,
                description=hit.description,
                severity=hit.severity,
                rule_name=hit.rule_name,
                status=AlertStatus.new,
                reasoning=hit.reasoning,
                owner_id=event.owner_id,
                correlation_key=correlation_key,
                attack_type=hit.attack_type,
                event_count=1,
                last_seen_at=event.timestamp,
            )
            db.add(alert)
            db.flush()
            incident = _create_incident_for_alert(db, alert, event)
            alert.incident_id = incident.id
            db.flush()
            if correlation_key:
                session_keys[correlation_key] = alert
            alerts.append(alert)

        return alerts


def _create_incident_for_alert(db: Session, alert: Alert, trigger_event: Event) -> Incident:
    inc = Incident(
        title=alert.title,
        summary=alert.description or alert.title,
        severity=alert.severity,
        status=IncidentStatus.open,
        owner_id=trigger_event.owner_id,
    )
    db.add(inc)
    db.flush()
    if trigger_event.id:
        inc.events.append(trigger_event)
    db.flush()
    return inc
