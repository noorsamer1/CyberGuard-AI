from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.ai_audit import AIAuditLog
from app.models.enums import IncidentStatus, ReportType, Severity
from app.models.report import Report
from app.core.deps import PaginationDep
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.incident import (
    IncidentBriefingOut,
    IncidentCreate,
    IncidentLinkEvents,
    IncidentOut,
    IncidentUpdate,
    incident_to_out,
)
from app.schemas.incident_portfolio import (
    IncidentPortfolioReportOut,
    PortfolioAIOut,
    PortfolioReportRequest,
)
from app.core.config import settings
from app.services import ai_service, briefing_service, incident_service, report_service
from app.services import incident_portfolio_service
from app.services.incident_service import get_incident
from app.tasks.ai_tasks import analyze_incident_task
from app.tasks.report_tasks import generate_incident_pdf_task

router = APIRouter()


@router.get("", response_model=PaginatedResponse[IncidentOut])
def list_incidents(
    user: CurrentUser,
    pagination: PaginationDep,
    db: Session = Depends(get_db),
    status: Optional[IncidentStatus] = None,
    severity: Optional[Severity] = None,
    q: Optional[str] = None,
):
    rows, total = incident_service.list_incidents(
        db,
        pagination.page,
        pagination.page_size,
        status=status,
        severity=severity,
        q=q,
        owner_id=user.id,
    )
    return PaginatedResponse(
        items=[incident_to_out(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("/portfolio-report", response_model=IncidentPortfolioReportOut)
def post_portfolio_report(
    user: CurrentUser,
    body: PortfolioReportRequest,
    db: Session = Depends(get_db),
):
    """Aggregate filtered incidents, deterministic charts, and optional AI narrative."""
    raw = incident_portfolio_service.build_portfolio_payload(
        db,
        owner_id=user.id,
        status=body.status,
        severity=body.severity,
        q=body.q,
        max_items=body.max_items,
    )
    ai_error: str | None = None
    ai_out: PortfolioAIOut | None = None

    if int(raw["stats"].get("total_matching") or 0) == 0:
        pass
    elif not settings.openrouter_api_key:
        ai_error = "OpenRouter API key is not configured; statistics and charts are still shown."
    else:
        ai_raw = ai_service.analyze_incident_portfolio(raw)
        if ai_raw:
            try:
                ai_out = PortfolioAIOut.model_validate(ai_raw)
            except Exception:
                ai_error = "AI returned an unexpected shape; showing statistics only."
        else:
            ai_error = "AI analysis did not return a result; showing statistics only."

    return IncidentPortfolioReportOut(
        generated_at=raw["generated_at"],
        filters=raw["filters"],
        max_items=raw["max_items"],
        truncated=raw["truncated"],
        truncation_note=raw["truncation_note"],
        stats=raw["stats"],
        charts=raw["charts"],
        ai=ai_out,
        ai_error=ai_error,
    )


@router.post("", response_model=IncidentOut)
def create_incident(user: CurrentUser, body: IncidentCreate, db: Session = Depends(get_db)):
    inc = incident_service.create_incident(db, body, owner_id=user.id)
    return incident_to_out(inc)


@router.get("/{incident_id}", response_model=IncidentOut)
def get_one(user: CurrentUser, incident_id: int, db: Session = Depends(get_db)):
    from app.core.exceptions import not_found
    inc = get_incident(db, incident_id)
    if inc.owner_id != user.id:
        raise not_found("Incident not found")
    return incident_to_out(inc)


@router.patch("/{incident_id}", response_model=IncidentOut)
def patch_incident(
    user: CurrentUser,
    incident_id: int,
    body: IncidentUpdate,
    db: Session = Depends(get_db),
):
    from app.core.exceptions import not_found
    inc = get_incident(db, incident_id, load_events=False)
    if inc.owner_id != user.id:
        raise not_found("Incident not found")
    updated = incident_service.update_incident(db, incident_id, body)
    return incident_to_out(updated)


@router.post("/{incident_id}/analyze", response_model=IncidentOut)
def analyze(
    user: CurrentUser,
    incident_id: int,
    db: Session = Depends(get_db),
    async_task: bool = Query(True),
):
    from app.core.exceptions import not_found
    inc = get_incident(db, incident_id, load_events=True)
    if inc.owner_id != user.id:
        raise not_found("Incident not found")
    if async_task:
        analyze_incident_task.delay(incident_id)
        return incident_to_out(inc)
    snippets = [
        {
            "ts": e.timestamp.isoformat(),
            "type": e.event_type,
            "src": e.source_ip,
            "msg": (e.message or "")[:500],
        }
        for e in inc.events[:40]
    ]
    result = ai_service.analyze_incident_context(inc.title, inc.summary, snippets)
    if result:
        inc.ai_summary = result.get("executive_summary") or result.get("summary")
        inc.remediation = result.get("remediation")
        inc.analyst_notes = result.get("analyst_notes")
        db.add(
            AIAuditLog(
                incident_id=inc.id,
                provider="openrouter",
                model="configured",
                prompt_type="incident_analyze",
                response_text=str(result)[:16000],
            )
        )
        db.commit()
    return incident_to_out(get_incident(db, incident_id))


@router.post("/{incident_id}/generate-report", response_model=MessageResponse)
def generate_report(
    user: CurrentUser,
    incident_id: int,
    email_copy: bool = Query(False),
    db: Session = Depends(get_db),
):
    from app.core.exceptions import not_found
    inc_check = get_incident(db, incident_id, load_events=True)
    if inc_check.owner_id != user.id:
        raise not_found("Incident not found")
    root = report_service.ensure_reports_dir()
    rep = Report(incident_id=incident_id, report_type=ReportType.incident_pdf, file_path="pending")
    db.add(rep)
    db.flush()
    path = root / f"incident_{incident_id}_{rep.id}.pdf"
    rep.file_path = str(path)
    db.commit()
    email_to = user.email if email_copy else None
    generate_incident_pdf_task.delay(rep.id, email_to=email_to)
    msg = f"Report {rep.id} queued"
    if email_copy:
        msg += (
            "; PDF will be emailed when generation finishes"
            if email_to
            else " (email not sent: no address on your account)"
        )
    return MessageResponse(message=msg)


@router.post("/{incident_id}/events", response_model=IncidentOut)
def link_events_route(
    user: CurrentUser,
    incident_id: int,
    body: IncidentLinkEvents,
    db: Session = Depends(get_db),
):
    from app.core.exceptions import not_found
    inc_check = get_incident(db, incident_id, load_events=False)
    if inc_check.owner_id != user.id:
        raise not_found("Incident not found")
    inc = incident_service.link_events(db, incident_id, body.event_ids, owner_id=user.id)
    return incident_to_out(inc)


@router.get("/{incident_id}/briefing", response_model=IncidentBriefingOut)
def get_briefing(
    user: CurrentUser,
    incident_id: int,
    db: Session = Depends(get_db),
    mode: str = Query("executive", pattern="^(executive|technical)$"),
):
    from app.core.exceptions import not_found

    inc = get_incident(db, incident_id)
    if inc.owner_id != user.id:
        raise not_found("Incident not found")
    return briefing_service.build_incident_briefing(db, inc, mode=mode)
