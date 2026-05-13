from datetime import timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class FailedLoginBurstRule(DetectionRule):
    name = "failed_login_burst"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        if not _is_failed_login(event):
            return []
        if not event.username:
            return []
        window_start = event.timestamp - timedelta(minutes=5)
        q = (
            select(func.count())
            .select_from(Event)
            .where(
                and_(
                    Event.username == event.username,
                    Event.timestamp >= window_start,
                    Event.timestamp <= event.timestamp,
                )
            )
        )
        cnt = db.scalar(q) or 0
        if cnt < 6:
            return []
        return [
            RuleHit(
                title="Failed login burst",
                description=f"User {event.username} has {cnt} failed login attempts in 5 minutes.",
                severity=Severity.medium,
                rule_name=self.name,
                reasoning="Threshold: ≥6 failed logins for same username within 5 minutes.",
                event_id=event.id,
            )
        ]


def _is_failed_login(event: Event) -> bool:
    et = (event.event_type or "").lower()
    st = (event.status or "").lower()
    msg = (event.message or "").lower()
    if "login" not in et and "auth" not in et:
        return False
    if st in ("failed", "failure", "denied", "error"):
        return True
    if "fail" in msg or "invalid" in msg:
        return True
    return False
