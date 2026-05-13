from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import bad_request, not_found
from app.models.alert import Alert
from app.models.enums import (
    AlertStatus,
    ExerciseActionType,
    ExerciseSessionStatus,
    IncidentStatus,
)
from app.models.exercise_action import ExerciseAction
from app.models.exercise_session import ExerciseSession
from app.models.incident import Incident
from app.schemas.exercise import (
    DoctorCoachRequest,
    DoctorCoachResponse,
    ExerciseActionCreate,
    ExerciseSessionCreate,
)
from app.services.event_service import EventService
from app.services.scenario_service import SCENARIOS, get_scenario_events

_event_service = EventService()


def list_sessions(
    db: Session, user_id: int, page: int, page_size: int
) -> tuple[list[ExerciseSession], int]:
    """Return paginated exercise sessions for one user."""
    stmt = (
        select(ExerciseSession)
        .where(ExerciseSession.user_id == user_id)
        .options(selectinload(ExerciseSession.actions))
    )
    total = (
        db.scalar(
            select(func.count()).select_from(ExerciseSession).where(ExerciseSession.user_id == user_id)
        )
        or 0
    )
    rows = db.scalars(
        stmt.order_by(ExerciseSession.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(rows), total


def get_session(db: Session, session_id: int, user_id: int) -> ExerciseSession:
    """Load one exercise session and enforce ownership."""
    session = db.scalar(
        select(ExerciseSession)
        .where(ExerciseSession.id == session_id, ExerciseSession.user_id == user_id)
        .options(selectinload(ExerciseSession.actions))
    )
    if not session:
        raise not_found("Exercise session not found")
    return session


def start_session(db: Session, user_id: int, payload: ExerciseSessionCreate) -> ExerciseSession:
    """Create a new timed exercise session and inject scenario telemetry."""
    if payload.scenario_id not in SCENARIOS:
        raise bad_request("Unknown scenario")
    now = datetime.now(timezone.utc)
    session = ExerciseSession(
        user_id=user_id,
        scenario_id=payload.scenario_id,
        status=ExerciseSessionStatus.active,
        duration_minutes=payload.duration_minutes,
        started_at=now,
        ends_at=now + timedelta(minutes=payload.duration_minutes),
    )
    db.add(session)

    # Launch scenario data at session start so students have real alerts/incidents to triage.
    scenario_events = get_scenario_events(payload.scenario_id)
    ingested_events, alerts = _event_service.ingest_batch(db, scenario_events, owner_id=user_id)

    session.result_json = {
        "scenario_bootstrap": {
            "events_ingested": len(ingested_events),
            "alerts_generated": len(alerts),
        }
    }
    db.commit()
    db.refresh(session)
    return get_session(db, session.id, user_id)


def add_action(
    db: Session, user_id: int, session_id: int, payload: ExerciseActionCreate
) -> ExerciseSession:
    """Append a student action and update hint counter if needed."""
    session = get_session(db, session_id, user_id)
    if session.status != ExerciseSessionStatus.active:
        raise bad_request("Session is not active")
    action = ExerciseAction(
        session_id=session.id,
        user_id=user_id,
        action_type=payload.action_type,
        target_type=payload.target_type,
        target_id=payload.target_id,
        notes=payload.notes,
    )
    db.add(action)
    if payload.action_type == ExerciseActionType.request_hint:
        session.hints_used = (session.hints_used or 0) + 1
    db.commit()
    return get_session(db, session_id, user_id)


def complete_session(db: Session, user_id: int, session_id: int) -> ExerciseSession:
    """Grade an exercise session and mark it completed."""
    session = get_session(db, session_id, user_id)
    if session.status != ExerciseSessionStatus.active:
        return session

    now = datetime.now(timezone.utc)
    window_end = min(now, session.ends_at)

    alerts_in_window = db.scalar(
        select(func.count())
        .select_from(Alert)
        .where(
            and_(
                Alert.owner_id == user_id,
                Alert.created_at >= session.started_at,
                Alert.created_at <= window_end,
            )
        )
    ) or 0
    incidents_in_window = db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(
            and_(
                Incident.owner_id == user_id,
                Incident.created_at >= session.started_at,
                Incident.created_at <= window_end,
            )
        )
    ) or 0

    ack_actions = _count_actions(session.actions, ExerciseActionType.acknowledge_alert)
    resolve_actions = _count_actions(session.actions, ExerciseActionType.resolve_alert)
    escalate_actions = _count_actions(session.actions, ExerciseActionType.escalate_incident)
    note_actions = _count_actions(session.actions, ExerciseActionType.add_note)

    detection_score = _ratio_score(ack_actions, max(alerts_in_window, 1))
    response_score = _ratio_score(resolve_actions + escalate_actions, max(alerts_in_window, 1))
    analysis_score = _ratio_score(escalate_actions + note_actions, max(incidents_in_window, 1))
    reporting_penalty = min(session.hints_used * 5, 30)
    reporting_score = max(100.0 - reporting_penalty, 50.0) if alerts_in_window > 0 else 100.0

    overall = round(
        (detection_score * 0.35)
        + (analysis_score * 0.25)
        + (response_score * 0.3)
        + (reporting_score * 0.1),
        2,
    )

    strengths: list[str] = []
    weaknesses: list[str] = []
    if detection_score >= 75:
        strengths.append("Strong alert triage coverage")
    else:
        weaknesses.append("Missed or delayed alert acknowledgements")
    if response_score >= 70:
        strengths.append("Good containment and response execution")
    else:
        weaknesses.append("Response actions were incomplete")
    if analysis_score >= 70:
        strengths.append("Good escalation and investigation flow")
    else:
        weaknesses.append("Investigation depth was limited")
    if session.hints_used == 0:
        strengths.append("Solved without hints")
    elif session.hints_used >= 3:
        weaknesses.append("High hint dependency")

    session.status = ExerciseSessionStatus.completed
    session.completed_at = now
    session.overall_score = overall
    session.detection_score = round(detection_score, 2)
    session.analysis_score = round(analysis_score, 2)
    session.response_score = round(response_score, 2)
    session.reporting_score = round(reporting_score, 2)
    session.strengths = "; ".join(strengths) if strengths else "Consistent baseline performance"
    session.weaknesses = "; ".join(weaknesses) if weaknesses else "No major weaknesses observed"
    session.result_json = {
        "alerts_in_window": alerts_in_window,
        "incidents_in_window": incidents_in_window,
        "actions": {
            "acknowledge_alert": ack_actions,
            "resolve_alert": resolve_actions,
            "escalate_incident": escalate_actions,
            "add_note": note_actions,
            "hints_used": session.hints_used,
        },
    }

    _auto_close_alerts(db, user_id, session.started_at, window_end)
    _auto_update_incidents(db, user_id, session.started_at, window_end)

    db.commit()
    return get_session(db, session_id, user_id)


def _count_actions(actions: list[ExerciseAction], action_type: ExerciseActionType) -> int:
    return sum(1 for action in actions if action.action_type == action_type)


def _ratio_score(numerator: int, denominator: int) -> float:
    return min(100.0, (numerator / max(denominator, 1)) * 100.0)


def _auto_close_alerts(db: Session, user_id: int, start: datetime, end: datetime) -> None:
    alerts = db.scalars(
        select(Alert).where(
            and_(Alert.owner_id == user_id, Alert.created_at >= start, Alert.created_at <= end)
        )
    ).all()
    for alert in alerts:
        if alert.status == AlertStatus.new:
            alert.status = AlertStatus.acknowledged


def _auto_update_incidents(db: Session, user_id: int, start: datetime, end: datetime) -> None:
    incidents = db.scalars(
        select(Incident).where(
            and_(Incident.owner_id == user_id, Incident.created_at >= start, Incident.created_at <= end)
        )
    ).all()
    for incident in incidents:
        if incident.status == IncidentStatus.open:
            incident.status = IncidentStatus.investigating


def doctor_teacher_mode(
    db: Session, user_id: int, payload: DoctorCoachRequest
) -> DoctorCoachResponse:
    """Generate targeted coaching feedback from a session's measured performance."""
    session = get_session(db, payload.session_id, user_id)

    detection = session.detection_score or 0.0
    analysis = session.analysis_score or 0.0
    response = session.response_score or 0.0
    reporting = session.reporting_score or 0.0

    weakest_area = min(
        {
            "alert triage": detection,
            "investigation depth": analysis,
            "response execution": response,
            "reporting discipline": reporting,
        }.items(),
        key=lambda item: item[1],
    )[0]
    diagnosis = (
        f"Session #{session.id} shows strongest performance in "
        f"{_best_area(detection, analysis, response, reporting)} and weaker execution in {weakest_area}."
    )
    likely_gap = (
        "Actions were logged, but sequencing and prioritization likely reduced score efficiency. "
        "Address high-severity alerts first, then escalate and document rapidly."
    )

    if payload.language == "ar":
        diagnosis = (
            f"الجلسة #{session.id} تظهر أداءً قويًا في {_best_area(detection, analysis, response, reporting, arabic=True)} "
            f"بينما تحتاج إلى تحسين في {weakest_area}."
        )
        likely_gap = (
            "تم تسجيل الإجراءات، لكن ترتيب الأولويات يحتاج تحسينًا. ابدأ دائمًا بالتنبيهات الحرجة "
            "ثم التصعيد والتوثيق."
        )

    coaching_steps = [
        "Filter queue to high/critical alerts and acknowledge within first 2 minutes.",
        "Escalate incidents with repeated indicators from the same source.",
        "Add one concise analyst note per major decision to preserve reasoning traceability.",
    ]
    quick_quiz = [
        "Which metric drops first when you ignore high-severity alerts?",
        "When should an alert become an incident in your flow?",
        "What evidence should be captured before marking an alert resolved?",
    ]
    if payload.language == "ar":
        coaching_steps = [
            "ابدأ بالتنبيهات high/critical واعمل Ack خلال أول دقيقتين.",
            "صعّد الحادثة عند تكرار المؤشرات من نفس المصدر.",
            "أضف ملاحظة تحليلية قصيرة لكل قرار مهم.",
        ]
        quick_quiz = [
            "أي مؤشر يتأثر أولاً عند تجاهل التنبيهات الحرجة؟",
            "متى يجب تحويل التنبيه إلى حادثة؟",
            "ما الأدلة المطلوبة قبل تحويل الحالة إلى Resolved؟",
        ]

    return DoctorCoachResponse(
        session_id=session.id,
        diagnosis=diagnosis,
        likely_gap=likely_gap,
        coaching_steps=coaching_steps,
        quick_quiz=quick_quiz,
    )


def _best_area(
    detection: float, analysis: float, response: float, reporting: float, arabic: bool = False
) -> str:
    labels = {
        "detection": "alert triage" if not arabic else "فرز التنبيهات",
        "analysis": "investigation depth" if not arabic else "عمق التحقيق",
        "response": "response execution" if not arabic else "تنفيذ الاستجابة",
        "reporting": "reporting discipline" if not arabic else "انضباط التوثيق",
    }
    area = max(
        {
            "detection": detection,
            "analysis": analysis,
            "response": response,
            "reporting": reporting,
        }.items(),
        key=lambda item: item[1],
    )[0]
    return labels[area]
