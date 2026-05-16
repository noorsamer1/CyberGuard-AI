from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class CommandInjectionRule(DetectionRule):
    name = "command_injection_attempt"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        del db
        if not _is_command_injection_signal(event):
            return []
        return [
            RuleHit(
                title="Command injection attempt",
                description="The local range target observed command-injection style input and blocked it.",
                severity=Severity.high,
                rule_name=self.name,
                reasoning=(
                    "Range rule: shell metacharacter payload or explicit command_injection metadata "
                    "was observed."
                ),
                event_id=event.id,
            )
        ]


def _is_command_injection_signal(event: Event) -> bool:
    metadata = event.metadata_json or {}
    if str(metadata.get("attack") or "").lower() == "command_injection":
        return True
    message = (event.message or "").lower()
    raw_log = (event.raw_log or "").lower()
    payload_tokens = (";", "&&", "|", "$(", "`", "whoami", " id")
    return any(token in message or token in raw_log for token in payload_tokens)
