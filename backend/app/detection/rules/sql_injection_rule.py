from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class SqlInjectionRule(DetectionRule):
    name = "sql_injection_attempt"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        del db
        msg = (event.message or "").lower()
        raw = (event.raw_log or "").lower()
        attack = ((event.metadata_json or {}).get("attack") or "").lower()
        if attack != "sql_injection" and not any(x in msg or x in raw for x in ("' or", " union ", "--", "drop table")):
            return []
        return [
            RuleHit(
                title="SQL injection attempt",
                description="The local range target observed SQL injection-style input against a toy endpoint.",
                severity=Severity.high,
                rule_name=self.name,
                attack_type="sql_injection",
                reasoning=(
                    "Evidence: SQL metacharacters or sql_injection metadata in "
                    f"{event.raw_log or event.message or 'web telemetry'}."
                ),
                event_id=event.id,
            )
        ]
