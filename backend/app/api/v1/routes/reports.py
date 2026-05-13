from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, PaginationDep
from app.core.exceptions import not_found
from app.models.incident import Incident
from app.models.report import Report
from app.schemas.common import PaginatedResponse
from app.schemas.report import ReportOut

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ReportOut])
def list_reports(
    user: CurrentUser,
    pagination: PaginationDep,
    db: Session = Depends(get_db),
):
    stmt = (
        select(Report)
        .join(Incident, Incident.id == Report.incident_id)
        .where(Incident.owner_id == user.id)
        .order_by(Report.created_at.desc())
    )
    total = (
        db.scalar(
            select(func.count())
            .select_from(Report)
            .join(Incident, Incident.id == Report.incident_id)
            .where(Incident.owner_id == user.id)
        )
        or 0
    )
    rows = db.scalars(
        stmt.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
    ).all()
    return PaginatedResponse(
        items=[ReportOut.model_validate(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{report_id}/download")
def download(user: CurrentUser, report_id: int, db: Session = Depends(get_db)):
    rep = db.scalar(
        select(Report)
        .join(Incident, Incident.id == Report.incident_id)
        .where(Report.id == report_id, Incident.owner_id == user.id)
    )
    if not rep or not Path(rep.file_path).is_file():
        raise not_found("Report file not ready")
    return FileResponse(
        rep.file_path,
        filename=Path(rep.file_path).name,
        media_type="application/pdf",
    )


@router.get("/{report_id}", response_model=ReportOut)
def get_report(user: CurrentUser, report_id: int, db: Session = Depends(get_db)):
    rep = db.scalar(
        select(Report)
        .join(Incident, Incident.id == Report.incident_id)
        .where(Report.id == report_id, Incident.owner_id == user.id)
    )
    if not rep:
        raise not_found()
    return ReportOut.model_validate(rep)
