from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.schemas.dashboard import DashboardCharts, DashboardSummary, UIRecommendation
from app.services import dashboard_service

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def summary(
    user: CurrentUser,
    db: Session = Depends(get_db),
    window: str = Query("24h", pattern="^(24h|7d|30d)$"),
):
    return dashboard_service.get_summary(db, owner_id=user.id, window=window)


@router.get("/charts", response_model=DashboardCharts)
def charts(
    user: CurrentUser,
    db: Session = Depends(get_db),
    window: str = Query("24h", pattern="^(24h|7d|30d)$"),
):
    return dashboard_service.get_charts(db, owner_id=user.id, window=window)


@router.get("/recent-incidents")
def recent_incidents(user: CurrentUser, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return dashboard_service.recent_incidents_table(db, owner_id=user.id)


@router.get("/recent-alerts")
def recent_alerts(user: CurrentUser, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return dashboard_service.recent_alerts_table(db, owner_id=user.id)


@router.get("/ui-recommendations", response_model=list[UIRecommendation])
def ui_recommendations(user: CurrentUser, db: Session = Depends(get_db)):
    return dashboard_service.get_ui_recommendations(db, owner_id=user.id)
