import csv
import io
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.detection.engine import DetectionEngine
from app.models.enums import Severity
from app.models.event import Event
from app.schemas.event import EventCreate

logger = get_logger(__name__)


def _event_from_create(data: EventCreate, owner_id: Optional[int] = None) -> Event:
    return Event(
        timestamp=data.timestamp,
        source_ip=data.source_ip,
        destination_ip=data.destination_ip,
        username=data.username,
        event_type=data.event_type,
        status=data.status,
        severity=data.severity,
        message=data.message,
        protocol=data.protocol,
        port=data.port,
        raw_log=data.raw_log,
        source_system=data.source_system,
        metadata_json=data.metadata,
        owner_id=owner_id,
    )


class EventService:
    def __init__(self, engine: Optional[DetectionEngine] = None) -> None:
        self.detection = engine or DetectionEngine()

    def _create_and_detect(
        self, db: Session, data: EventCreate, owner_id: Optional[int] = None
    ) -> tuple[Event, list]:
        ev = _event_from_create(data, owner_id=owner_id)
        db.add(ev)
        db.flush()
        alerts = self.detection.run(db, ev)
        return ev, alerts

    def create_event(
        self, db: Session, data: EventCreate, owner_id: Optional[int] = None
    ) -> tuple[Event, list]:
        ev, alerts = self._create_and_detect(db, data, owner_id=owner_id)
        db.commit()
        db.refresh(ev)
        _queue_ai_classification([ev.id])
        return ev, alerts

    def ingest_batch(
        self, db: Session, items: list[EventCreate], owner_id: Optional[int] = None
    ) -> tuple[list[Event], list]:
        all_alerts: list = []
        events: list[Event] = []
        for item in items:
            ev, alerts = self._create_and_detect(db, item, owner_id=owner_id)
            events.append(ev)
            all_alerts.extend(alerts)
        db.commit()
        for ev in events:
            db.refresh(ev)
        _queue_ai_classification([ev.id for ev in events])
        return events, all_alerts

    def list_events(
        self,
        db: Session,
        page: int,
        page_size: int,
        severity: Optional[Severity] = None,
        source_ip: Optional[str] = None,
        event_type: Optional[str] = None,
        q: Optional[str] = None,
        owner_id: Optional[int] = None,
    ) -> tuple[list[Event], int]:
        stmt = select(Event)
        count_stmt = select(func.count()).select_from(Event)
        conds = []
        if owner_id is not None:
            conds.append(Event.owner_id == owner_id)
        if severity:
            conds.append(Event.severity == severity)
        if source_ip:
            conds.append(Event.source_ip == source_ip)
        if event_type:
            conds.append(Event.event_type == event_type)
        if q:
            like = f"%{q}%"
            conds.append(
                or_(
                    Event.message.ilike(like),
                    Event.raw_log.ilike(like),
                    Event.username.ilike(like),
                )
            )
        if conds:
            stmt = stmt.where(and_(*conds))
            count_stmt = count_stmt.where(and_(*conds))
        total = db.scalar(count_stmt) or 0
        stmt = stmt.order_by(Event.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = list(db.scalars(stmt).all())
        return rows, total

    def get(self, db: Session, event_id: int) -> Optional[Event]:
        return db.get(Event, event_id)

    def parse_upload(self, filename: str, raw: bytes) -> list[EventCreate]:
        text = raw.decode("utf-8", errors="replace")
        lower = filename.lower()
        if lower.endswith(".json"):
            return _parse_json_upload(text)
        if lower.endswith(".csv"):
            return _parse_csv_upload(text)
        return _parse_lines_upload(text)


def _parse_json_upload(text: str) -> list[EventCreate]:
    data = json.loads(text)
    if isinstance(data, list):
        return [EventCreate.model_validate(x) for x in data]
    if isinstance(data, dict) and "events" in data:
        return [EventCreate.model_validate(x) for x in data["events"]]
    return [EventCreate.model_validate(data)]


def _parse_csv_upload(text: str) -> list[EventCreate]:
    reader = csv.DictReader(io.StringIO(text))
    out: list[EventCreate] = []
    for row in reader:
        row = {k.strip().lower().replace(" ", "_"): (v.strip() if v else None) for k, v in row.items()}
        ts_raw = row.get("timestamp") or row.get("time")
        if not ts_raw:
            continue
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        except ValueError:
            ts = datetime.now(timezone.utc)
        sev = (row.get("severity") or "low").lower()
        try:
            severity = Severity(sev)
        except ValueError:
            severity = Severity.low
        out.append(
            EventCreate(
                timestamp=ts,
                source_ip=row.get("source_ip"),
                destination_ip=row.get("destination_ip"),
                username=row.get("username"),
                event_type=row.get("event_type") or "generic",
                status=row.get("status"),
                severity=severity,
                message=row.get("message"),
                protocol=row.get("protocol"),
                port=int(row["port"]) if row.get("port") and str(row["port"]).isdigit() else None,
                raw_log=row.get("raw_log"),
                source_system=row.get("source_system"),
            )
        )
    return out


def _parse_lines_upload(text: str) -> list[EventCreate]:
    now = datetime.now(timezone.utc)
    return [
        EventCreate(
            timestamp=now,
            event_type="log_line",
            message=line[:2000],
            raw_log=line[:8000],
            severity=Severity.low,
        )
        for line in text.splitlines()
        if line.strip()
    ]


def _queue_ai_classification(event_ids: list[int]) -> None:
    if not settings.ai_detection_enabled or not event_ids:
        return
    try:
        from app.tasks.ai_tasks import classify_events_task

        max_items = max(settings.ai_detection_max_events_per_task, 1)
        for idx in range(0, len(event_ids), max_items):
            classify_events_task.delay(event_ids[idx : idx + max_items])
    except Exception as exc:
        logger.warning("AI classification queue failed; continuing without AI enrichment: %s", exc)
