from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.services.event_service import EventService
from app.services.scenario_service import SCENARIOS, get_scenario_events

router = APIRouter()
_svc = EventService()


@router.get("")
def list_scenarios(_: CurrentUser):
    return [asdict(meta) for meta in SCENARIOS.values()]


@router.post("/{scenario_id}/run")
def run_scenario(scenario_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    meta = SCENARIOS[scenario_id]
    events = get_scenario_events(scenario_id)
    _svc.ingest_batch(db, events, owner_id=user.id)
    return {
        "scenario_id": scenario_id,
        "name": meta.name,
        "events_ingested": len(events),
        "message": "Scenario launched. Check Alerts & Incidents for detections.",
    }
