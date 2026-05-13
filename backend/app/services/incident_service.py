from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import not_found
from app.models.enums import IncidentStatus, Severity
from app.models.event import Event
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate


def list_incidents(
    db: Session,
    page: int,
    page_size: int,
    status: Optional[IncidentStatus] = None,
    severity: Optional[Severity] = None,
    q: Optional[str] = None,
    owner_id: Optional[int] = None,
) -> tuple[list[Incident], int]:
    stmt = select(Incident).options(selectinload(Incident.events))
    count_stmt = select(func.count()).select_from(Incident)
    conds = []
    if owner_id is not None:
        conds.append(Incident.owner_id == owner_id)
    if status:
        conds.append(Incident.status == status)
    if severity:
        conds.append(Incident.severity == severity)
    if q:
        like = f"%{q}%"
        conds.append(or_(Incident.title.ilike(like), Incident.summary.ilike(like)))
    if conds:
        stmt = stmt.where(and_(*conds))
        count_stmt = count_stmt.where(and_(*conds))
    total = db.scalar(count_stmt) or 0
    stmt = stmt.order_by(Incident.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return list(db.scalars(stmt).unique().all()), total


def get_incident(db: Session, incident_id: int, load_events: bool = True) -> Incident:
    stmt = select(Incident).where(Incident.id == incident_id)
    if load_events:
        stmt = stmt.options(selectinload(Incident.events))
    inc = db.scalars(stmt).first()
    if not inc:
        raise not_found("Incident not found")
    return inc


def create_incident(
    db: Session, data: IncidentCreate, owner_id: Optional[int] = None
) -> Incident:
    inc = Incident(
        title=data.title,
        summary=data.summary,
        severity=data.severity,
        status=data.status,
        owner_id=owner_id,
    )
    db.add(inc)
    db.flush()
    for eid in data.event_ids:
        ev = db.get(Event, eid)
        if ev and (owner_id is None or ev.owner_id == owner_id):
            inc.events.append(ev)
    db.commit()
    db.refresh(inc)
    return get_incident(db, inc.id)


def update_incident(db: Session, incident_id: int, data: IncidentUpdate) -> Incident:
    inc = get_incident(db, incident_id, load_events=False)
    if data.title is not None:
        inc.title = data.title
    if data.summary is not None:
        inc.summary = data.summary
    if data.severity is not None:
        inc.severity = data.severity
    if data.status is not None:
        inc.status = data.status
        if data.status == IncidentStatus.resolved and not inc.resolved_at:
            inc.resolved_at = datetime.now(timezone.utc)
    if data.analyst_notes is not None:
        inc.analyst_notes = data.analyst_notes
    if data.resolved_at is not None:
        inc.resolved_at = data.resolved_at
    inc.updated_at = datetime.now(timezone.utc)
    db.commit()
    return get_incident(db, incident_id)


def link_events(
    db: Session, incident_id: int, event_ids: list[int], owner_id: Optional[int] = None
) -> Incident:
    inc = get_incident(db, incident_id, load_events=True)
    for eid in event_ids:
        ev = db.get(Event, eid)
        if ev and (owner_id is None or ev.owner_id == owner_id) and ev not in inc.events:
            inc.events.append(ev)
    db.commit()
    return get_incident(db, incident_id)
