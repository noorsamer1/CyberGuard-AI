from datetime import timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class DeniedSpikeRule(DetectionRule):
    name = "denied_access_spike"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        if not event.source_ip:
            return []
        if not _is_denied(event):
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
                        func.lower(Event.status).in_(["denied", "blocked", "forbidden"]),
                        func.lower(Event.message).like("%denied%"),
                    ),
                )
            )
        )
        cnt = db.scalar(q) or 0
        if cnt < 20:
            return []
        return [
            RuleHit(
                title="Denied access spike",
                description=f"Source {event.source_ip} triggered {cnt} denied/blocked events in 5 minutes.",
                severity=Severity.low,
                rule_name=self.name,
                attack_type="denied_access_spike",
                reasoning=(
                    f"Evidence: {cnt} denied/blocked events from {event.source_ip} within 5 minutes."
                ),
                event_id=event.id,
            )
        ]


def _is_denied(event: Event) -> bool:
    st = (event.status or "").lower()
    msg = (event.message or "").lower()
    return st in ("denied", "blocked", "forbidden") or "denied" in msg
