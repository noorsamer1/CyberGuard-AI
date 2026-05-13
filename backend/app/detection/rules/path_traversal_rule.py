from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class PathTraversalRule(DetectionRule):
    name = "path_traversal_attempt"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        del db
        msg = (event.message or "").lower()
        raw = (event.raw_log or "").lower()
        attack = ((event.metadata_json or {}).get("attack") or "").lower()
        if attack != "path_traversal" and "../" not in msg and "../" not in raw and "..\\" not in raw:
            return []
        return [
            RuleHit(
                title="Path traversal attempt",
                description="The local range target blocked traversal-style file path input.",
                severity=Severity.high,
                rule_name=self.name,
                reasoning="Range rule: traversal sequence or explicit path_traversal metadata was observed.",
                event_id=event.id,
            )
        ]
