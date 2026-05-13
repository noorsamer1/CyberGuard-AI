from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class SuspiciousUploadRule(DetectionRule):
    name = "suspicious_upload_misuse"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        del db
        attack = ((event.metadata_json or {}).get("attack") or "").lower()
        msg = (event.message or "").lower()
        if attack != "upload_misuse" and "suspicious upload" not in msg:
            return []
        return [
            RuleHit(
                title="Suspicious upload misuse",
                description="The local range target observed suspicious upload behavior.",
                severity=Severity.medium,
                rule_name=self.name,
                reasoning="Range rule: upload misuse metadata or suspicious upload wording was observed.",
                event_id=event.id,
            )
        ]
