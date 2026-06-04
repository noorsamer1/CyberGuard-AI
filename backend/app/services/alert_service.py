from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.models.alert import Alert
from app.models.enums import AlertStatus, Severity


def list_alerts(
    db: Session,
    page: int,
    page_size: int,
    severity: Optional[Severity] = None,
    status: Optional[AlertStatus] = None,
    rule_name: Optional[str] = None,
    q: Optional[str] = None,
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
    owner_id: Optional[int] = None,
) -> tuple[list[Alert], int]:
    stmt = select(Alert)
    count_stmt = select(func.count()).select_from(Alert)
    conds = []
    if owner_id is not None:
        conds.append(Alert.owner_id == owner_id)
    if severity:
        conds.append(Alert.severity == severity)
    if status:
        conds.append(Alert.status == status)
    if rule_name:
        conds.append(Alert.rule_name == rule_name)
    if q:
        like = f"%{q}%"
        conds.append(or_(Alert.title.ilike(like), Alert.description.ilike(like)))
    if from_ts:
        conds.append(Alert.created_at >= from_ts)
    if to_ts:
        conds.append(Alert.created_at <= to_ts)
    if conds:
        stmt = stmt.where(and_(*conds))
        count_stmt = count_stmt.where(and_(*conds))
    total = db.scalar(count_stmt) or 0
    stmt = stmt.order_by(Alert.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return list(db.scalars(stmt).all()), total


def get_alert(db: Session, alert_id: int) -> Alert:
    a = db.get(Alert, alert_id)
    if not a:
        raise not_found("Alert not found")
    return a


def update_status(db: Session, alert_id: int, status: AlertStatus) -> Alert:
    a = get_alert(db, alert_id)
    a.status = status
    a.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(a)
    return a


def list_alerts_for_report(
    db: Session,
    *,
    owner_id: int,
    severity: Optional[Severity] = None,
    status: Optional[AlertStatus] = None,
    limit: int = 500,
) -> list[Alert]:
    """Load alerts with linked events for portfolio PDF (newest first)."""
    from sqlalchemy.orm import selectinload

    stmt = (
        select(Alert)
        .options(selectinload(Alert.event))
        .where(Alert.owner_id == owner_id)
        .order_by(Alert.created_at.desc())
        .limit(limit)
    )
    conds = []
    if severity:
        conds.append(Alert.severity == severity)
    if status:
        conds.append(Alert.status == status)
    if conds:
        stmt = stmt.where(and_(*conds))
    return list(db.scalars(stmt).all())
