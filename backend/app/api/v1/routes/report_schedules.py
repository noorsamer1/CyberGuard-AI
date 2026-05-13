import io

from fastapi import APIRouter, Depends, HTTPException, status
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.enums import ReportScheduleFrequency
from app.models.report_schedule import ReportSchedule
from app.models.user import User
from app.schemas.report_schedule import (
    MessageResponse,
    ReportScheduleCreate,
    ReportScheduleOut,
    ReportScheduleUpdate,
)
from app.services.email_service import send_pdf_email

router = APIRouter()


def _smtp_test_pdf_bytes() -> bytes:
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=letter)
    c.setTitle("SMTP test")
    c.drawString(72, 720, "CyberGuard AI — SMTP test")
    c.save()
    return buf.getvalue()


@router.get("", response_model=list[ReportScheduleOut])
def list_schedules(user: CurrentUser, db: Session = Depends(get_db)):
    rows = db.scalars(select(ReportSchedule).where(ReportSchedule.user_id == user.id)).all()
    return rows


@router.post("", response_model=ReportScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(
    user: CurrentUser,
    body: ReportScheduleCreate,
    db: Session = Depends(get_db),
):
    weekly_day = None
    if body.frequency == ReportScheduleFrequency.weekly:
        weekly_day = 0 if body.weekly_day_utc is None else body.weekly_day_utc
    row = ReportSchedule(
        user_id=user.id,
        min_severity=body.min_severity,
        frequency=body.frequency,
        recipient_email=str(body.recipient_email),
        enabled=body.enabled,
        preferred_time_utc=body.preferred_time_utc,
        weekly_day_utc=weekly_day,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{schedule_id}", response_model=ReportScheduleOut)
def update_schedule(
    user: CurrentUser,
    schedule_id: int,
    body: ReportScheduleUpdate,
    db: Session = Depends(get_db),
):
    row = db.get(ReportSchedule, schedule_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    data = body.model_dump(exclude_unset=True)
    if "recipient_email" in data and data["recipient_email"] is not None:
        data["recipient_email"] = str(data["recipient_email"])
    for k, v in data.items():
        setattr(row, k, v)
    if row.frequency != ReportScheduleFrequency.weekly:
        row.weekly_day_utc = None
    elif row.weekly_day_utc is None:
        row.weekly_day_utc = 0
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(user: CurrentUser, schedule_id: int, db: Session = Depends(get_db)):
    row = db.get(ReportSchedule, schedule_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(row)
    db.commit()
    return None


@router.post("/test-email", response_model=MessageResponse)
def test_smtp_email(user: CurrentUser, db: Session = Depends(get_db)):
    if not settings.smtp_configured:
        raise HTTPException(
            status_code=400,
            detail="SMTP not configured. Set SMTP_HOST and SMTP_FROM in the API environment.",
        )
    u = db.get(User, user.id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    send_pdf_email(
        to_addrs=[u.email],
        subject="CyberGuard AI — SMTP test",
        body_text="This is a test message. Scheduled digests will attach a PDF report.",
        pdf_bytes=_smtp_test_pdf_bytes(),
        filename="smtp-test.pdf",
    )
    return MessageResponse(message=f"Test email sent to {u.email}")
