from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class PrivilegeEscalationRule(DetectionRule):
    name = "privilege_escalation_suspected"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        del db
        if not _is_privilege_escalation_signal(event):
            return []
        actor = event.username or event.source_ip or "unknown actor"
        return [
            RuleHit(
                title="Privilege escalation behavior detected",
                description=f"Suspicious privilege escalation activity was observed for {actor}.",
                severity=Severity.critical,
                rule_name=self.name,
                reasoning=(
                    "Range rule: privilege-escalation metadata or suspicious admin-access escalation "
                    "keywords were observed."
                ),
                event_id=event.id,
            )
        ]


def _is_privilege_escalation_signal(event: Event) -> bool:
    metadata = event.metadata_json or {}
    if str(metadata.get("attack") or "").lower() == "privilege_escalation":
        return True
    event_type = (event.event_type or "").lower()
    if event_type not in ("admin_access", "authentication", "endpoint"):
        return False
    text = f"{event.message or ''} {event.raw_log or ''}".lower()
    return any(
        marker in text
        for marker in ("sudo", "token::elevate", "administrator", "privilege escalation", "runas")
    )
