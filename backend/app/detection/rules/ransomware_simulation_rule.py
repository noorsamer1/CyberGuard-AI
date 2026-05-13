from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class RansomwareSimulationRule(DetectionRule):
    name = "ransomware_simulation"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        del db
        msg = (event.message or "").lower()
        raw = (event.raw_log or "").lower()
        attack = ((event.metadata_json or {}).get("attack") or "").lower()
        if attack != "ransomware_simulation" and "ransomware" not in msg and ".locked" not in raw:
            return []
        return [
            RuleHit(
                title="Ransomware behavior simulation",
                description="The local range target observed safe ransomware-like behavior against dummy files.",
                severity=Severity.critical,
                rule_name=self.name,
                reasoning="Range rule: ransomware simulation metadata, blocked payload, or .locked rename artifact was observed.",
                event_id=event.id,
            )
        ]
