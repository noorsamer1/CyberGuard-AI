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
        query = str((event.metadata_json or {}).get("query") or "")[:80]
        return [
            RuleHit(
                title="Potential DNS tunneling activity",
                description=(
                    f"Source {event.source_ip} generated {suspicious_count} suspicious DNS tunneling "
                    "signals in 5 minutes."
                ),
                severity=Severity.high,
                rule_name=self.name,
                attack_type="dns_tunneling",
                reasoning=(
                    f"Evidence: {suspicious_count} suspicious DNS events from {event.source_ip} "
                    f"within 5 minutes (sample query={query or 'encoded label'})."
                ),
                event_id=event.id,
            )
        ]


def _is_dns_tunneling_signal(event: Event) -> bool:
    metadata = event.metadata_json or {}
    if str(metadata.get("attack") or "").lower() == "dns_tunneling":
        return True
    if (event.event_type or "").lower() != "dns":
        return False
    message = (event.message or "").lower()
    if "suspicious dns query" in message:
        return True
    query = str(metadata.get("query") or "")
    if len(query) > 32:
        return True
    return False
