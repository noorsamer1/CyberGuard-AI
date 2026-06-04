from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.models.ai_audit import AIAuditLog
from app.models.incident import Incident
from app.services import ai_detection_service
from app.services import ai_service
from app.services.incident_report_context import build_incident_report_context, context_to_dict
from app.tasks.celery_app import celery_app


def _apply_incident_ai_result(db, inc: Incident, result: dict) -> None:
    inc.ai_summary = result.get("executive_summary") or result.get("summary")
    inc.remediation = result.get("prioritized_remediation") or result.get("remediation")
    note_parts = []
    if result.get("root_cause"):
        note_parts.append(f"Root cause: {result['root_cause']}")
    if result.get("impact"):
        note_parts.append(f"Impact: {result['impact']}")
    if result.get("why_suspicious"):
        note_parts.append(f"Why suspicious: {result['why_suspicious']}")
    if result.get("analyst_notes"):
        note_parts.append(str(result["analyst_notes"]))
    inc.analyst_notes = "\n\n".join(note_parts) or None
    db.add(
        AIAuditLog(
            incident_id=inc.id,
            provider="openrouter",
            model="configured",
            prompt_type="incident_analyze",
            response_text=str(result)[:16000],
        )
    )


@celery_app.task(name="incidents.analyze_ai")
def analyze_incident_task(incident_id: int) -> str:
    db = SessionLocal()
    try:
        inc = db.scalars(
            select(Incident)
            .options(selectinload(Incident.events))
            .where(Incident.id == incident_id)
        ).first()
        if not inc:
            return "missing"
        snippets = [
            {
                "ts": e.timestamp.isoformat(),
                "type": e.event_type,
                "src": e.source_ip,
                "msg": (e.message or "")[:500],
            }
            for e in inc.events[:40]
        ]
        det_ctx = context_to_dict(build_incident_report_context(db, inc))
        result = ai_service.analyze_incident_context(
            inc.title, inc.summary, snippets, deterministic_context=det_ctx
        )
        if not result:
            return "skipped"
        _apply_incident_ai_result(db, inc, result)
        db.commit()
        return "ok"
    finally:
        db.close()


@celery_app.task(name="events.classify_ai")
def classify_events_task(event_ids: list[int]) -> str:
    db = SessionLocal()
    try:
        count = ai_detection_service.classify_events(db, event_ids)
        return f"ok:{count}"
    finally:
        db.close()
