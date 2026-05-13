from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, PaginationDep
from app.models.enums import ExerciseActionType
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.exercise import (
    DoctorCoachRequest,
    DoctorCoachResponse,
    ExerciseActionCreate,
    ExerciseScenarioOut,
    ExerciseSessionCreate,
    ExerciseSessionOut,
)
from app.services import learning_service
from app.services.scenario_service import SCENARIOS

router = APIRouter()


@router.get("/scenarios", response_model=list[ExerciseScenarioOut])
def list_scenarios(_: CurrentUser):
    return [ExerciseScenarioOut.model_validate(asdict(meta)) for meta in SCENARIOS.values()]


@router.post("/sessions", response_model=ExerciseSessionOut)
def start_session(user: CurrentUser, body: ExerciseSessionCreate, db: Session = Depends(get_db)):
    session = learning_service.start_session(db, user.id, body)
    return ExerciseSessionOut.model_validate(session)


@router.get("/sessions", response_model=PaginatedResponse[ExerciseSessionOut])
def list_sessions(
    user: CurrentUser,
    pagination: PaginationDep,
    db: Session = Depends(get_db),
):
    rows, total = learning_service.list_sessions(db, user.id, pagination.page, pagination.page_size)
    return PaginatedResponse(
        items=[ExerciseSessionOut.model_validate(row) for row in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/sessions/{session_id}", response_model=ExerciseSessionOut)
def get_session(user: CurrentUser, session_id: int, db: Session = Depends(get_db)):
    session = learning_service.get_session(db, session_id, user.id)
    return ExerciseSessionOut.model_validate(session)


@router.post("/sessions/{session_id}/actions", response_model=ExerciseSessionOut)
def add_action(
    user: CurrentUser,
    session_id: int,
    body: ExerciseActionCreate,
    db: Session = Depends(get_db),
):
    session = learning_service.add_action(db, user.id, session_id, body)
    return ExerciseSessionOut.model_validate(session)


@router.post("/sessions/{session_id}/complete", response_model=ExerciseSessionOut)
def complete_session(user: CurrentUser, session_id: int, db: Session = Depends(get_db)):
    session = learning_service.complete_session(db, user.id, session_id)
    return ExerciseSessionOut.model_validate(session)


@router.post("/sessions/{session_id}/hint", response_model=MessageResponse)
def request_hint(user: CurrentUser, session_id: int, db: Session = Depends(get_db)):
    learning_service.add_action(
        db,
        user.id,
        session_id,
        ExerciseActionCreate(action_type=ExerciseActionType.request_hint, notes="Hint requested"),
    )
    return MessageResponse(
        message="Hint: Prioritize high/critical alerts first, then escalate incidents that remain open."
    )


@router.post("/doctor-mode", response_model=DoctorCoachResponse)
def doctor_mode(user: CurrentUser, body: DoctorCoachRequest, db: Session = Depends(get_db)):
    return learning_service.doctor_teacher_mode(db, user.id, body)
