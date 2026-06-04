from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event

_SHELL_TOKENS = (";", "&&", "|", "$(", "`", "whoami", " id")


class CommandInjectionRule(DetectionRule):
    name = "command_injection_attempt"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        del db
        if not _is_command_injection_signal(event):
            return []
        evidence = _evidence_snippet(event)
        return [
            RuleHit(
                title="Command injection attempt",
                description="The local range target observed command-injection style input and blocked it.",
                severity=Severity.high,
                rule_name=self.name,
                attack_type="command_injection",
                reasoning=(
                    "Evidence: command-injection indicators in telemetry — "
                    f"{evidence}"
                ),
                event_id=event.id,
            )
        ]


def _is_command_injection_signal(event: Event) -> bool:
    metadata = event.metadata_json or {}
    if str(metadata.get("attack") or "").lower() == "command_injection":
        return True
    if (event.event_type or "").lower() != "web_attack":
        return False
    message = (event.message or "").lower()
    raw_log = (event.raw_log or "").lower()
    return any(token in message or token in raw_log for token in _SHELL_TOKENS)


def _evidence_snippet(event: Event) -> str:
    metadata = event.metadata_json or {}
    payload = metadata.get("payload")
    if payload:
        return f"payload={str(payload)[:120]}"
    return (event.raw_log or event.message or "shell metacharacters detected")[:160]
