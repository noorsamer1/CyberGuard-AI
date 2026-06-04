from datetime import timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.detection.rules.base import DetectionRule, RuleHit
from app.models.enums import Severity
from app.models.event import Event

_MAX_PORTS_IN_TEXT = 40


def _format_port_list(ports: list[int]) -> str:
    if not ports:
        return "(none)"
    head = ports[:_MAX_PORTS_IN_TEXT]
    s = ", ".join(str(p) for p in head)
    extra = len(ports) - len(head)
    if extra > 0:
        s += f" (+{extra} more)"
    return s


class PortScanRule(DetectionRule):
    name = "port_scan"

    def evaluate(self, db: Session, event: Event) -> list[RuleHit]:
        if not event.source_ip or event.port is None:
            return []
        window_start = event.timestamp - timedelta(minutes=2)
        window_filter = and_(
            Event.source_ip == event.source_ip,
            Event.timestamp >= window_start,
            Event.timestamp <= event.timestamp,
            Event.port.isnot(None),
        )
        q = select(func.count(func.distinct(Event.port))).select_from(Event).where(window_filter)
        distinct_ports = db.scalar(q) or 0
        if distinct_ports < 15:
            return []
        ports_stmt = select(Event.port).where(window_filter).distinct().order_by(Event.port)
        ports_sorted = list(db.scalars(ports_stmt).all())
        ports_line = _format_port_list(ports_sorted)
        description = (
            f"Source {event.source_ip} touched {distinct_ports} distinct ports in 2 minutes. "
            f"Ports: {ports_line}."
        )
        return [
            RuleHit(
                title="Possible port scan",
                description=description,
                severity=Severity.medium,
                rule_name=self.name,
                attack_type="port_scan",
                reasoning=(
                    f"Evidence: {distinct_ports} distinct ports from {event.source_ip} in 2 minutes "
                    f"(ports include {ports_line})."
                ),
                event_id=event.id,
            )
        ]
