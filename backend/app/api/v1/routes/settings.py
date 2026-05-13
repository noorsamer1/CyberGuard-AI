from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.alert import Alert
from app.models.event import Event
from app.models.incident import Incident
from app.models.report import Report
from app.models.user import User
from app.schemas.settings import NotificationPrefs, SettingsOut

router = APIRouter()


@router.delete("/reset", status_code=200)
def reset_all_data(user: CurrentUser, db: Session = Depends(get_db)):
    own_incident_ids = select(Incident.id).where(Incident.owner_id == user.id)
    db.execute(delete(Report).where(Report.incident_id.in_(own_incident_ids)))
    db.execute(delete(Incident).where(Incident.owner_id == user.id))
    db.execute(delete(Alert).where(Alert.owner_id == user.id))
    db.execute(delete(Event).where(Event.owner_id == user.id))
    db.commit()
    return {"message": "Your events, alerts, incidents, and reports have been deleted."}


@router.get("", response_model=SettingsOut)
def get_settings(user: CurrentUser, db: Session = Depends(get_db)):
    u = db.get(User, user.id)
    if not u:
        return SettingsOut(
            notification_prefs=NotificationPrefs(),
            demo_mode_hint="POST /api/v1/events/synthetic?strong=true for the full SOC demo, or ?count=80 for random traffic.",
        )
    return SettingsOut(
        notification_prefs=NotificationPrefs(
            email_alerts=u.notify_email,
            push_alerts=u.notify_push,
        ),
        demo_mode_hint="POST /api/v1/events/synthetic?strong=true for the full SOC demo, or ?count=80 for random traffic.",
    )


@router.patch("/notifications", response_model=SettingsOut)
def patch_notifications(
    user: CurrentUser,
    body: NotificationPrefs,
    db: Session = Depends(get_db),
):
    u = db.get(User, user.id)
    if not u:
        return SettingsOut(
            notification_prefs=body,
            demo_mode_hint="User not found.",
        )
    u.notify_email = body.email_alerts
    u.notify_push = body.push_alerts
    db.commit()
    db.refresh(u)
    return SettingsOut(
        notification_prefs=NotificationPrefs(
            email_alerts=u.notify_email,
            push_alerts=u.notify_push,
        ),
        demo_mode_hint="Notification preferences saved to your account.",
    )
