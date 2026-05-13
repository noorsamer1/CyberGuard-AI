from typing import Optional

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.exceptions import not_found
from app.models.enums import Severity
from app.core.deps import PaginationDep
from app.schemas.common import PaginatedResponse
from app.schemas.ai_classification import AIClassificationOut, ai_classification_to_out
from app.schemas.event import EventCreate, EventIngestBatch, EventOut, event_to_out
from app.services import ai_detection_service
from app.services.event_service import EventService
from app.services.synthetic_service import generate_strong_demo_events, generate_synthetic_events

router = APIRouter()
_event_service = EventService()


async def _broadcast_alerts(request: Request, alerts) -> None:
    mgr = getattr(request.app.state, "ws_manager", None)
    if not mgr or not alerts:
        return
    from app.schemas.alert import alert_to_out

    for a in alerts:
        try:
            payload = alert_to_out(a).model_dump(mode="json")
            await mgr.broadcast({"type": "alert", "payload": payload})
        except Exception:
            pass


@router.post("/ingest", response_model=list[EventOut])
async def ingest(
    user: CurrentUser,
    request: Request,
    body: EventIngestBatch,
    db: Session = Depends(get_db),
):
    events, alerts = _event_service.ingest_batch(db, body.events, owner_id=user.id)
    await _broadcast_alerts(request, alerts)
    return [event_to_out(e) for e in events]


@router.post("/single", response_model=EventOut)
async def ingest_single(
    user: CurrentUser,
    request: Request,
    body: EventCreate,
    db: Session = Depends(get_db),
):
    ev, alerts = _event_service.create_event(db, body, owner_id=user.id)
    await _broadcast_alerts(request, alerts)
    return event_to_out(ev)


@router.post("/upload", response_model=list[EventOut])
async def upload(
    user: CurrentUser,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    items = _event_service.parse_upload(file.filename or "upload.txt", raw)
    events, alerts = _event_service.ingest_batch(db, items, owner_id=user.id)
    await _broadcast_alerts(request, alerts)
    return [event_to_out(e) for e in events]


@router.post("/synthetic", response_model=list[EventOut])
async def synthetic(
    user: CurrentUser,
    request: Request,
    db: Session = Depends(get_db),
    count: int = Query(40, ge=1, le=500),
    strong: bool = Query(
        False,
        description="If true, ingest the full scripted demo (brute force, port scan, spikes, rate anomaly). Ignores count.",
    ),
):
    items = generate_strong_demo_events() if strong else generate_synthetic_events(count)
    events, alerts = _event_service.ingest_batch(db, items, owner_id=user.id)
    await _broadcast_alerts(request, alerts)
    return [event_to_out(e) for e in events]


@router.get("", response_model=PaginatedResponse[EventOut])
def list_events(
    user: CurrentUser,
    pagination: PaginationDep,
    db: Session = Depends(get_db),
    severity: Optional[Severity] = None,
    source_ip: Optional[str] = None,
    event_type: Optional[str] = None,
    q: Optional[str] = None,
):
    rows, total = _event_service.list_events(
        db,
        pagination.page,
        pagination.page_size,
        severity=severity,
        source_ip=source_ip,
        event_type=event_type,
        q=q,
        owner_id=user.id,
    )
    return PaginatedResponse(
        items=[event_to_out(e) for e in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{event_id}", response_model=EventOut)
def get_event(
    user: CurrentUser,
    event_id: int,
    db: Session = Depends(get_db),
):
    ev = _event_service.get(db, event_id)
    if not ev or ev.owner_id != user.id:
        raise not_found()
    return event_to_out(ev)


@router.get("/{event_id}/ai-classification", response_model=AIClassificationOut)
def get_event_ai_classification(
    user: CurrentUser,
    event_id: int,
    db: Session = Depends(get_db),
):
    ev = _event_service.get(db, event_id)
    if not ev or ev.owner_id != user.id:
        raise not_found()
    item = ai_detection_service.get_event_classification(db, event_id, owner_id=user.id)
    if not item:
        raise not_found("AI classification not found")
    return ai_classification_to_out(item)
