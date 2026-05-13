from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Severity
from app.schemas.ai_classification import AIClassificationOut, ai_classification_to_out


class EventBase(BaseModel):
    timestamp: datetime
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    username: Optional[str] = None
    event_type: str = Field(..., max_length=128)
    status: Optional[str] = None
    severity: Severity = Severity.low
    message: Optional[str] = None
    protocol: Optional[str] = None
    port: Optional[int] = None
    raw_log: Optional[str] = None
    source_system: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class EventCreate(EventBase):
    pass


class EventIngestBatch(BaseModel):
    events: list[EventCreate]


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    username: Optional[str] = None
    event_type: str
    status: Optional[str] = None
    severity: Severity
    message: Optional[str] = None
    protocol: Optional[str] = None
    port: Optional[int] = None
    raw_log: Optional[str] = None
    source_system: Optional[str] = None
    metadata: Optional[dict[str, Any]] = Field(default=None, validation_alias="metadata_json")
    ai_assessment: Optional[AIClassificationOut] = None
    created_at: datetime


def event_to_out(e) -> EventOut:
    return EventOut(
        id=e.id,
        timestamp=e.timestamp,
        source_ip=e.source_ip,
        destination_ip=e.destination_ip,
        username=e.username,
        event_type=e.event_type,
        status=e.status,
        severity=e.severity,
        message=e.message,
        protocol=e.protocol,
        port=e.port,
        raw_log=e.raw_log,
        source_system=e.source_system,
        metadata=e.metadata_json,
        ai_assessment=ai_classification_to_out(getattr(e, "ai_classification", None)),
        created_at=e.created_at,
    )
