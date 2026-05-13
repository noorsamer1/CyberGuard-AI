from datetime import timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class BruteForceRule(DetectionRule):
    name = "brute_force"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        if not event.source_ip:
            return []
        if not _is_auth_failure(event):
            return []
        window_start = event.timestamp - timedelta(minutes=5)
        q = (
            select(func.count())
            .select_from(Event)
            .where(
                and_(
                    Event.source_ip == event.source_ip,
                    Event.timestamp >= window_start,
                    Event.timestamp <= event.timestamp,
                    or_(
                        Event.status.in_(["failed", "failure", "denied", "error"]),
                        func.lower(Event.event_type).like("%login%"),
                    ),
                )
            )
        )
        cnt = db.scalar(q) or 0
        if cnt < 10:
            return []
        return [
            RuleHit(
                title="Possible brute-force attack",
                description=f"Source {event.source_ip} shows {cnt} authentication failures in 5 minutes.",
                severity=Severity.high,
                rule_name=self.name,
                reasoning="Threshold: ≥10 auth-related failures from one IP within 5 minutes.",
                event_id=event.id,
            )
        ]


def _is_auth_failure(event: Event) -> bool:
    st = (event.status or "").lower()
    et = (event.event_type or "").lower()
    if st in ("failed", "failure", "denied", "error"):
        return True
    if "login" in et or "auth" in et:
        return st in ("failed", "failure", "denied", "error") or "fail" in (event.message or "").lower()
    return False
