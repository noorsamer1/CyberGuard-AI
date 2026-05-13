from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.detection.rules.brute_force_rule import BruteForceRule
from app.detection.rules.data_exfiltration_rule import DataExfiltrationRule
from app.detection.rules.denied_spike_rule import DeniedSpikeRule
from app.detection.rules.failed_login_rule import FailedLoginBurstRule
from app.detection.rules.path_traversal_rule import PathTraversalRule
from app.detection.rules.port_scan_rule import PortScanRule
from app.detection.rules.ransomware_simulation_rule import RansomwareSimulationRule
from app.detection.rules.rate_anomaly_rule import RateAnomalyRule
from app.detection.rules.sql_injection_rule import SqlInjectionRule
from app.detection.rules.suspicious_upload_rule import SuspiciousUploadRule
from app.models.alert import Alert
from app.models.enums import AlertStatus, IncidentStatus, Severity
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
        ]

    def run(self, db: Session, event: Event) -> list[Alert]:
        hits: list[RuleHit] = []
        for rule in self.rules:
            hits.extend(rule.evaluate(db, event))
        alerts: list[Alert] = []
        for h in hits:
            alert = Alert(
                event_id=h.event_id,
                title=h.title,
                description=h.description,
                severity=h.severity,
                rule_name=h.rule_name,
                status=AlertStatus.new,
                reasoning=h.reasoning,
                owner_id=event.owner_id,
            )
            db.add(alert)
            alerts.append(alert)
        db.flush()
        for a in alerts:
            _ensure_incident_for_alert(db, a, event)
        return alerts


def _ensure_incident_for_alert(db: Session, alert: Alert, trigger_event: Event) -> None:
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
