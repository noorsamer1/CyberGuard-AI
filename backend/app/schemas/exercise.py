from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ExerciseActionType, ExerciseSessionStatus


class ExerciseScenarioOut(BaseModel):
    id: str
    name: str
    description: str
    severity: str
    mitre_tactics: list[str]
    mitre_techniques: list[str]
    threat_actor: str
    estimated_alerts: int
    duration_minutes: int


class ExerciseSessionCreate(BaseModel):
    scenario_id: str = Field(..., min_length=1, max_length=128)
    duration_minutes: int = Field(10, ge=5, le=120)


class ExerciseActionCreate(BaseModel):
    action_type: ExerciseActionType
    target_type: Optional[str] = Field(default=None, max_length=64)
    target_id: Optional[int] = None
    notes: Optional[str] = None


class ExerciseActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    user_id: int
    action_type: ExerciseActionType
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime


class ExerciseSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    scenario_id: str
    status: ExerciseSessionStatus
    duration_minutes: int
    started_at: datetime
    ends_at: datetime
    completed_at: Optional[datetime] = None
    overall_score: Optional[float] = None
    detection_score: Optional[float] = None
    analysis_score: Optional[float] = None
    response_score: Optional[float] = None
    reporting_score: Optional[float] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    hints_used: int
    result_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    actions: list[ExerciseActionOut] = Field(default_factory=list)


class DoctorCoachRequest(BaseModel):
    session_id: int
    question: str = Field(..., min_length=3, max_length=2000)
    language: str = Field("en", pattern="^(en|ar)$")


class DoctorCoachResponse(BaseModel):
    session_id: int
    diagnosis: str
    likely_gap: str
    coaching_steps: list[str] = Field(default_factory=list)
    quick_quiz: list[str] = Field(default_factory=list)
