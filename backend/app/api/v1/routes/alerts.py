from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.enums import AlertStatus, Severity
from app.schemas.ai_classification import AIClassificationOut, ai_classification_to_out
from app.schemas.alert import AlertOut, AlertStatusUpdate, alert_to_out
from app.core.deps import PaginationDep
from app.schemas.common import PaginatedResponse
from app.services import alert_service
from app.services import ai_detection_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[AlertOut])
def list_alerts(
    user: CurrentUser,
    pagination: PaginationDep,
    db: Session = Depends(get_db),
    severity: Optional[Severity] = None,
    status: Optional[AlertStatus] = None,
    rule_name: Optional[str] = None,
    q: Optional[str] = None,
    from_ts: Optional[datetime] = Query(None),
    to_ts: Optional[datetime] = Query(None),
):
    rows, total = alert_service.list_alerts(
        db,
        pagination.page,
        pagination.page_size,
        severity=severity,
        status=status,
        rule_name=rule_name,
        q=q,
        from_ts=from_ts,
        to_ts=to_ts,
        owner_id=user.id,
    )
    return PaginatedResponse(
        items=[alert_to_out(a) for a in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(user: CurrentUser, alert_id: int, db: Session = Depends(get_db)):
    from app.core.exceptions import not_found
    a = alert_service.get_alert(db, alert_id)
    if a.owner_id != user.id:
        raise not_found("Alert not found")
    return alert_to_out(a)


@router.get("/{alert_id}/ai-classification", response_model=AIClassificationOut)
def get_alert_ai_classification(user: CurrentUser, alert_id: int, db: Session = Depends(get_db)):
    from app.core.exceptions import not_found

    a = alert_service.get_alert(db, alert_id)
    if a.owner_id != user.id:
        raise not_found("Alert not found")
    item = ai_detection_service.get_alert_classification(db, a, owner_id=user.id)
    if not item:
        raise not_found("AI classification not found")
    return ai_classification_to_out(item)


@router.patch("/{alert_id}/status", response_model=AlertOut)
def patch_status(
    user: CurrentUser,
    alert_id: int,
    body: AlertStatusUpdate,
    db: Session = Depends(get_db),
):
    from app.core.exceptions import not_found
    a = alert_service.get_alert(db, alert_id)
    if a.owner_id != user.id:
        raise not_found("Alert not found")
    a = alert_service.update_status(db, alert_id, body.status)
    return alert_to_out(a)
