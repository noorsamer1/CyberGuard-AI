from datetime import timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class PasswordSprayRule(DetectionRule):
    name = "password_spray"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        if not event.source_ip:
            return []
        if not _is_password_spray_signal(event):
            return []

        window_start = event.timestamp - timedelta(minutes=10)
        unique_users = db.scalar(
            select(func.count(func.distinct(Event.username)))
            .select_from(Event)
            .where(
                and_(
                    Event.source_ip == event.source_ip,
                    Event.timestamp >= window_start,
                    Event.timestamp <= event.timestamp,
                    Event.username.isnot(None),
                    Event.event_type == "authentication",
                    func.lower(Event.status).in_(["failed", "failure", "denied", "error"]),
                )
            )
        ) or 0
        if unique_users < 8:
            return []
        return [
            RuleHit(
                title="Password spray campaign suspected",
                description=(
                    f"Source {event.source_ip} failed authentication against "
                    f"{unique_users} distinct usernames in 10 minutes."
                ),
                severity=Severity.high,
                rule_name=self.name,
                reasoning=(
                    "Threshold: >=8 unique usernames with failed authentication from one source "
                    "within 10 minutes."
                ),
                event_id=event.id,
            )
        ]


def _is_password_spray_signal(event: Event) -> bool:
    event_type = (event.event_type or "").lower()
    status = (event.status or "").lower()
    metadata = event.metadata_json or {}
    if str(metadata.get("attack") or "").lower() == "password_spray":
        return True
    if event_type != "authentication":
        return False
    if status in ("failed", "failure", "denied", "error"):
        return "spray" in (event.message or "").lower()
    return False
