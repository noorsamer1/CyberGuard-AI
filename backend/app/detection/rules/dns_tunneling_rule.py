from datetime import timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class DnsTunnelingRule(DetectionRule):
    name = "dns_tunneling_suspected"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        if not event.source_ip:
            return []
        if not _is_dns_tunneling_signal(event):
            return []

        window_start = event.timestamp - timedelta(minutes=5)
        suspicious_count = db.scalar(
            select(func.count())
            .select_from(Event)
            .where(
                and_(
                    Event.source_ip == event.source_ip,
                    Event.timestamp >= window_start,
                    Event.timestamp <= event.timestamp,
                    Event.event_type == "dns",
                    or_(
                        func.lower(Event.message).like("%suspicious dns query%"),
                        func.lower(Event.raw_log).like("%dns_query%"),
                    ),
                )
            )
        ) or 0
        if suspicious_count < 4:
            return []
        return [
            RuleHit(
                title="Potential DNS tunneling activity",
                description=(
                    f"Source {event.source_ip} generated {suspicious_count} suspicious DNS tunneling "
                    "signals in 5 minutes."
                ),
                severity=Severity.high,
                rule_name=self.name,
                reasoning=(
                    "Threshold: >=4 suspicious DNS query events from one source in 5 minutes "
                    "(long/encoded query behavior)."
                ),
                event_id=event.id,
            )
        ]


def _is_dns_tunneling_signal(event: Event) -> bool:
    event_type = (event.event_type or "").lower()
    message = (event.message or "").lower()
    raw_log = (event.raw_log or "").lower()
    metadata = event.metadata_json or {}
    query = str(metadata.get("query") or "").lower()
    if str(metadata.get("attack") or "").lower() == "dns_tunneling":
        return True
    if event_type != "dns":
        return False
    if "suspicious dns query" in message:
        return True
    if len(query) > 32 and "." in query:
        return True
    if "dns_query" in raw_log and ("credential" in raw_log or "chunk" in raw_log):
        return True
    return False
