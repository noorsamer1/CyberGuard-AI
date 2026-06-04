from datetime import timedelta

from sqlalchemy import and_, func, or_, select
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
                    _failed_login_filter(),
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
                attack_type="brute_force",
                reasoning=(
                    f"Evidence: {cnt} failed logins for user {event.username} within 5 minutes "
                    f"(latest status={event.status or 'unknown'})."
                ),
                event_id=event.id,
            )
        ]


def _failed_login_filter():
    """SQLAlchemy filter for failed authentication events only."""
    return or_(
        Event.status.in_(["failed", "failure", "denied", "error"]),
        and_(
            func.lower(Event.event_type).like("%login%"),
            func.lower(Event.message).like("%failed%"),
            ~func.lower(Event.message).like("%successful%"),
        ),
        and_(
            func.lower(Event.event_type).like("%auth%"),
            func.lower(Event.message).like("%failed%"),
            ~func.lower(Event.message).like("%successful%"),
        ),
    )


def _is_failed_login(event: Event) -> bool:
    et = (event.event_type or "").lower()
    st = (event.status or "").lower()
    msg = (event.message or "").lower()
    if "login" not in et and "auth" not in et:
        return False
    if st in ("success", "ok", "succeeded"):
        return False
    if "successful" in msg:
        return False
    if st in ("failed", "failure", "denied", "error"):
        return True
    if "failed login" in msg or "invalid" in msg:
        return True
    return False
