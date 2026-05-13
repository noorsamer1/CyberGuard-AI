from datetime import timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class RateAnomalyRule(DetectionRule):
    name = "event_rate_anomaly"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        if not event.source_ip:
            return []
        window_start = event.timestamp - timedelta(minutes=1)
        q = (
            select(func.count())
            .select_from(Event)
            .where(
                and_(
                    Event.source_ip == event.source_ip,
                    Event.timestamp >= window_start,
                    Event.timestamp <= event.timestamp,
                )
            )
        )
        cnt = db.scalar(q) or 0
        if cnt < 80:
            return []
        return [
            RuleHit(
                title="Abnormal event rate",
                description=f"Source {event.source_ip} generated {cnt} events in one minute.",
                severity=Severity.critical,
                rule_name=self.name,
                reasoning="Threshold: ≥80 events from one IP within 1 minute.",
                event_id=event.id,
            )
        ]
