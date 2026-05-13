import socket
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.schemas.alert import alert_to_out
from app.schemas.range import RangeRunResult, RangeScenarioOut, RangeStatus
from app.services.event_service import EventService
from app.services.range_service import RANGE_SCENARIOS, RangeAttackRunner, logs_to_events

router = APIRouter()
_events = EventService()


async def _broadcast_alerts(request: Request, alerts) -> None:
    mgr = getattr(request.app.state, "ws_manager", None)
    if not mgr or not alerts:
        return
    for alert in alerts:
        try:
            await mgr.broadcast({"type": "alert", "payload": alert_to_out(alert).model_dump(mode="json")})
        except Exception:
            pass


def _range_target_hostname() -> str:
    parsed = urlparse(settings.range_target_url)
    return parsed.hostname or "range-target"


def _resolve_range_target_ip() -> str | None:
    host = _range_target_hostname()
    try:
        return socket.gethostbyname(host)
    except OSError:
        return None


def _api_runner_hostname() -> str:
    try:
        return socket.gethostname()
    except OSError:
        return "unknown"


def _result(
    *,
    scenario_id: str,
    name: str,
    requests_executed: int,
    logs_collected: int,
    events_ingested: int,
    alerts_generated: int,
    message: str,
) -> RangeRunResult:
    return RangeRunResult(
        scenario_id=scenario_id,
        name=name,
        requests_executed=requests_executed,
        logs_collected=logs_collected,
        events_ingested=events_ingested,
        alerts_generated=alerts_generated,
        incidents_created=alerts_generated,
        message=message,
    )


@router.get("/status", response_model=RangeStatus)
def range_status(_: CurrentUser):
    runner = RangeAttackRunner()
    healthy, message = runner.status()
    return RangeStatus(
        enabled=settings.range_enabled,
        target_url=settings.range_target_url,
        public_url=settings.range_public_url,
        healthy=healthy,
        message=message,
        range_target_hostname=_range_target_hostname(),
        range_target_ip=_resolve_range_target_ip(),
        api_runner_hostname=_api_runner_hostname(),
    )


@router.get("/scenarios", response_model=list[RangeScenarioOut])
def list_range_scenarios(_: CurrentUser):
    runner = RangeAttackRunner()
    return [RangeScenarioOut.model_validate(runner.scenario_public(s)) for s in RANGE_SCENARIOS.values()]


@router.post("/scenarios/{scenario_id}/run", response_model=RangeRunResult)
async def run_range_scenario(
    scenario_id: str,
    user: CurrentUser,
    request: Request,
    db: Session = Depends(get_db),
):
    runner = RangeAttackRunner()
    scenario, requests_executed, logs = runner.run(scenario_id)
    events = logs_to_events(logs)
    ingested, alerts = _events.ingest_batch(db, events, owner_id=user.id) if events else ([], [])
    await _broadcast_alerts(request, alerts)
    return _result(
        scenario_id=scenario.id,
        name=scenario.name,
        requests_executed=requests_executed,
        logs_collected=len(logs),
        events_ingested=len(ingested),
        alerts_generated=len(alerts),
        message="Range scenario executed against the local controlled target.",
    )


@router.post("/collect", response_model=RangeRunResult)
async def collect_range_logs(
    user: CurrentUser,
    request: Request,
    db: Session = Depends(get_db),
):
    runner = RangeAttackRunner()
    logs = runner.drain_logs()
    events = logs_to_events(logs)
    ingested, alerts = _events.ingest_batch(db, events, owner_id=user.id) if events else ([], [])
    await _broadcast_alerts(request, alerts)
    return _result(
        scenario_id="manual_collect",
        name="Manual Range Log Collection",
        requests_executed=0,
        logs_collected=len(logs),
        events_ingested=len(ingested),
        alerts_generated=len(alerts),
        message="Collected local range logs and ingested them into CyberGuard.",
    )


@router.post("/reset", response_model=RangeRunResult)
def reset_range(_: CurrentUser):
    runner = RangeAttackRunner()
    runner.reset()
    return _result(
        scenario_id="range_reset",
        name="Range Reset",
        requests_executed=1,
        logs_collected=0,
        events_ingested=0,
        alerts_generated=0,
        message="Local range target was reset. CyberGuard users and historical data were not deleted.",
    )
