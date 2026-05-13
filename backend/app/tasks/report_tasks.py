import logging
from datetime import datetime, time as dt_time, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.alert import Alert
from app.models.enums import ReportScheduleFrequency
from app.models.event import Event
from app.models.incident import Incident
from app.models.report import Report
from app.models.report_schedule import ReportSchedule
from app.services.email_service import send_pdf_email
from app.services.incident_service import get_incident
from app.services.report_service import (
    build_digest_pdf,
    build_incident_pdf,
    digest_severity_filter_label,
    ensure_reports_dir,
    incidents_matching_digest_min_severity,
)
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="reports.generate_pdf")
def generate_incident_pdf_task(report_id: int, email_to: str | None = None) -> str:
    db = SessionLocal()
    try:
        rep = db.get(Report, report_id)
        if not rep:
            return "missing"
        inc = get_incident(db, rep.incident_id, load_events=True)
        ensure_reports_dir()
        path = Path(rep.file_path)
        build_incident_pdf(inc, path)
        db.commit()
        if email_to and settings.smtp_configured:
            try:
                pdf_bytes = path.read_bytes()
                send_pdf_email(
                    to_addrs=[email_to],
                    subject=f"CyberGuard AI — incident #{inc.id} report",
                    body_text=(
                        f"Attached: PDF report for incident #{inc.id}\n"
                        f"Title: {inc.title or '—'}\n"
                        f"Severity: {inc.severity.value}\n"
                    ),
                    pdf_bytes=pdf_bytes,
                    filename=path.name,
                )
            except Exception:
                logger.exception("Failed to email incident report report_id=%s", report_id)
        elif email_to and not settings.smtp_configured:
            logger.info("SMTP not configured; incident PDF saved only at %s", path)
        return str(path)
    finally:
        db.close()


def _digest_interval(s: ReportSchedule) -> timedelta:
    if s.frequency == ReportScheduleFrequency.hourly:
        return timedelta(hours=1)
    if s.frequency == ReportScheduleFrequency.twice_daily:
        return timedelta(hours=12)
    if s.frequency == ReportScheduleFrequency.daily:
        return timedelta(days=1)
    return timedelta(days=7)


def _digest_window(s: ReportSchedule, window_end: datetime) -> tuple[datetime, datetime]:
    if s.frequency == ReportScheduleFrequency.hourly:
        return window_end - timedelta(hours=1), window_end
    if s.frequency == ReportScheduleFrequency.twice_daily:
        return window_end - timedelta(hours=12), window_end
    if s.frequency == ReportScheduleFrequency.daily:
        return window_end - timedelta(days=1), window_end
    return window_end - timedelta(days=7), window_end


def _freq_label(s: ReportSchedule) -> str:
    return {
        ReportScheduleFrequency.hourly: "hourly",
        ReportScheduleFrequency.twice_daily: "every 12 hours",
        ReportScheduleFrequency.daily: "daily",
        ReportScheduleFrequency.weekly: "weekly",
    }[s.frequency]


def _parse_preferred_time_utc(s: ReportSchedule) -> tuple[int, int] | None:
    raw = (s.preferred_time_utc or "").strip()
    if not raw:
        return None
    parts = raw.split(":")
    if len(parts) != 2:
        return None
    try:
        h, m = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if 0 <= h <= 23 and 0 <= m <= 59:
        return h, m
    return None


def _schedule_due_interval_only(s: ReportSchedule, now: datetime) -> bool:
    interval = _digest_interval(s)
    if s.last_run_at is None:
        return True
    lr = s.last_run_at
    if lr.tzinfo is None:
        lr = lr.replace(tzinfo=timezone.utc)
    return (now - lr) >= interval


def _daily_time_due(last_run: datetime | None, now: datetime, h: int, m: int) -> bool:
    now = now.astimezone(timezone.utc)
    if last_run is None:
        slot = datetime.combine(now.date(), dt_time(h, m), tzinfo=timezone.utc)
        return now >= slot
    lr = last_run.astimezone(timezone.utc)
    next_run = datetime.combine(lr.date() + timedelta(days=1), dt_time(h, m), tzinfo=timezone.utc)
    return now >= next_run


def _next_weekly_slot_on_or_after(start: datetime, target_weekday: int, h: int, m: int) -> datetime:
    start = start.astimezone(timezone.utc)
    for i in range(14):
        d = start.date() + timedelta(days=i)
        if d.weekday() != target_weekday:
            continue
        cand = datetime.combine(d, dt_time(h, m), tzinfo=timezone.utc)
        if cand >= start:
            return cand
    return datetime.combine(
        start.date() + timedelta(days=14), dt_time(h, m), tzinfo=timezone.utc
    )


def _weekly_time_due(last_run: datetime | None, now: datetime, wd: int, h: int, m: int) -> bool:
    now = now.astimezone(timezone.utc)
    if last_run is None:
        slot = _next_weekly_slot_on_or_after(now, wd, h, m)
        return now >= slot
    lr = last_run.astimezone(timezone.utc)
    next_slot = _next_weekly_slot_on_or_after(lr + timedelta(seconds=1), wd, h, m)
    return now >= next_slot


def _latest_twice_daily_slot_leq(now: datetime, h: int, m: int) -> datetime | None:
    now = now.astimezone(timezone.utc)
    best: datetime | None = None
    d0 = now.date() - timedelta(days=2)
    for k in range(5):
        d = d0 + timedelta(days=k)
        a = datetime.combine(d, dt_time(h, m), tzinfo=timezone.utc)
        for slot in (a, a + timedelta(hours=12)):
            if slot <= now and (best is None or slot > best):
                best = slot
    return best


def _twice_daily_time_due(last_run: datetime | None, now: datetime, h: int, m: int) -> bool:
    latest = _latest_twice_daily_slot_leq(now, h, m)
    if latest is None:
        return False
    if last_run is None:
        return True
    return last_run.astimezone(timezone.utc) < latest


def _schedule_due(s: ReportSchedule, now: datetime) -> bool:
    tt = _parse_preferred_time_utc(s)
    if tt is None:
        return _schedule_due_interval_only(s, now)
    h, m = tt
    lr = s.last_run_at
    if lr is not None and lr.tzinfo is None:
        lr = lr.replace(tzinfo=timezone.utc)

    if s.frequency == ReportScheduleFrequency.hourly:
        return _schedule_due_interval_only(s, now)

    if s.frequency == ReportScheduleFrequency.daily:
        return _daily_time_due(lr, now, h, m)

    if s.frequency == ReportScheduleFrequency.weekly:
        wd = s.weekly_day_utc if s.weekly_day_utc is not None else 0
        return _weekly_time_due(lr, now, wd, h, m)

    if s.frequency == ReportScheduleFrequency.twice_daily:
        return _twice_daily_time_due(lr, now, h, m)

    return _schedule_due_interval_only(s, now)


@celery_app.task(name="reports.run_due_schedules")
def run_due_report_schedules() -> str:
    now = datetime.now(timezone.utc)
    db = SessionLocal()
    processed = 0
    try:
        schedules = db.scalars(select(ReportSchedule).where(ReportSchedule.enabled.is_(True))).all()
        for s in schedules:
            if not _schedule_due(s, now):
                continue
            window_end = now
            window_start, window_end = _digest_window(s, window_end)

            incidents = db.scalars(
                select(Incident).where(
                    Incident.created_at >= window_start,
                    Incident.created_at <= window_end,
                )
            ).all()

            events_count = (
                db.scalar(
                    select(func.count()).select_from(Event).where(
                        Event.timestamp >= window_start,
                        Event.timestamp <= window_end,
                    )
                )
                or 0
            )
            alerts_count = (
                db.scalar(
                    select(func.count()).select_from(Alert).where(
                        Alert.created_at >= window_start,
                        Alert.created_at <= window_end,
                    )
                )
                or 0
            )

            filtered = incidents_matching_digest_min_severity(list(incidents), s.min_severity)
            if len(filtered) == 0:
                logger.info(
                    "Digest schedule_id=%s: no incidents match severity filter in window; skipping PDF and email",
                    s.id,
                )
                s.last_run_at = now
                db.commit()
                processed += 1
                continue

            root = ensure_reports_dir()
            path = root / f"digest_u{s.user_id}_{now.strftime('%Y%m%d%H%M%S')}.pdf"
            build_digest_pdf(
                path=path,
                window_start=window_start,
                window_end=window_end,
                min_severity=s.min_severity,
                incidents=list(incidents),
                events_count=int(events_count),
                alerts_count=int(alerts_count),
            )
            pdf_bytes = path.read_bytes()
            freq_label = _freq_label(s)
            sev_note = digest_severity_filter_label(s.min_severity)
            body = (
                f"Your {freq_label} CyberGuard AI security digest is attached.\n\n"
                f"Window (UTC): {window_start.isoformat()} — {window_end.isoformat()}\n"
                f"Severity filter: {sev_note}\n"
                '(Minimum threshold: only incidents at or above this level are included; the list can be all "high" if nothing else matched.)\n'
            )
            if settings.smtp_configured:
                try:
                    send_pdf_email(
                        to_addrs=[s.recipient_email],
                        subject=f"CyberGuard AI digest ({freq_label})",
                        body_text=body,
                        pdf_bytes=pdf_bytes,
                        filename=path.name,
                    )
                except Exception:
                    logger.exception("Failed to email digest schedule_id=%s", s.id)
            else:
                logger.info("SMTP not configured; digest saved only at %s", path)

            s.last_run_at = now
            db.commit()
            processed += 1
    finally:
        db.close()
    return f"processed={processed}"
