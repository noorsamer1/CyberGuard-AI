from fastapi import APIRouter

from app.api.v1.routes import (
    alerts,
    auth,
    dashboard,
    events,
    incidents,
    range,
    report_schedules,
    reports,
    scenarios,
    settings,
    users,
    websocket,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(range.router, prefix="/range", tags=["range"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(report_schedules.router, prefix="/report-schedules", tags=["report-schedules"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(websocket.router, tags=["websocket"])
