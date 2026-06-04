from datetime import timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event


class DataExfiltrationRule(DetectionRule):
    name = "data_exfiltration"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        if not event.source_ip:
            return []
        if not _is_exfil_signal(event):
            return []
        window_start = event.timestamp - timedelta(minutes=10)
        count = db.scalar(
            select(func.count())
            .select_from(Event)
            .where(
                and_(
                    Event.source_ip == event.source_ip,
                    Event.timestamp >= window_start,
                    Event.timestamp <= event.timestamp,
                    or_(
                        func.lower(Event.event_type).in_(["dlp", "firewall"]),
                        func.lower(Event.message).like("%exfil%"),
                        func.lower(Event.message).like("%sensitive file access%"),
                        func.lower(Event.message).like("%large outbound data transfer%"),
                        func.lower(Event.raw_log).like("%bytes=%mb%"),
                    ),
                )
            )
        ) or 0
        if count < 4:
            return []
        return [
            RuleHit(
                title="Potential data exfiltration campaign",
                description=(
                    f"Source {event.source_ip} generated {count} exfiltration-like signals in 10 minutes "
                    "(DLP access + outbound transfer pattern)."
                ),
                severity=Severity.critical,
                rule_name=self.name,
                attack_type="data_exfiltration",
                reasoning=(
                    f"Evidence: {count} exfil indicators from {event.source_ip} within 10 minutes "
                    f"(latest: {event.message or event.raw_log or 'DLP/network signal'})."
                ),
                event_id=event.id,
            )
        ]


def _is_exfil_signal(event: Event) -> bool:
    event_type = (event.event_type or "").lower()
    message = (event.message or "").lower()
    raw_log = (event.raw_log or "").lower()
    if event_type in ("dlp", "firewall"):
        return True
    if "exfil" in message or "sensitive file access" in message:
        return True
    if "large outbound data transfer" in message:
        return True
    if "bytes=" in raw_log and "mb" in raw_log:
        return True
    return False
