"""Tests for alert correlation — one alert per attack within window."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.models.incident import Incident
from app.schemas.event import EventCreate
from app.services.event_service import EventService
from app.services.range_service import logs_to_events
from tests.fixtures.range_logs import _log


@pytest.fixture(autouse=True)
def enable_correlation(monkeypatch):
    monkeypatch.setattr(settings, "correlation_enabled", True)
    monkeypatch.setattr(settings, "correlation_window_minutes", 30)


def _command_event(offset: int, payload: str, *, attack: bool) -> EventCreate:
    metadata = {"payload": payload}
    if attack:
        metadata["attack"] = "command_injection"
    raw = _log(
        timestamp=(datetime(2026, 5, 30, 12, 0, offset, tzinfo=timezone.utc)).isoformat(),
        event_type="web_attack" if attack else "web",
        status="blocked" if attack else "ok",
        severity="high" if attack else "low",
        message=f"Command injection payload blocked: {payload}" if attack else f"Safe: {payload}",
        raw_log=f"POST /exec payload={payload}",
        metadata=metadata,
    )
    return logs_to_events([raw])[0]


def test_same_attack_correlates_to_one_alert(db_session) -> None:
    service = EventService()
    events = [
        _command_event(0, "a; whoami", attack=True),
        _command_event(1, "b && id", attack=True),
        _command_event(2, "c | nc", attack=True),
    ]
    _, alerts = service.ingest_batch(db_session, events)
    assert len(alerts) == 1
    db_session.refresh(alerts[0])
    assert alerts[0].event_count == 3
    assert alerts[0].attack_type == "command_injection"
    assert alerts[0].incident_id is not None


def test_different_attack_types_create_separate_alerts(db_session) -> None:
    service = EventService()
    cmd = logs_to_events(
        [
            _log(
                event_type="web_attack",
                status="blocked",
                severity="high",
                message="Command injection payload blocked: x; id",
                metadata={"attack": "command_injection", "payload": "x; id"},
            )
        ]
    )
    sqli = logs_to_events(
        [
            _log(
                event_type="web_attack",
                status="blocked",
                severity="high",
                message="SQL injection attempt against search query: ' OR 1=1--",
                metadata={"attack": "sql_injection"},
            )
        ]
    )
    _, alerts = service.ingest_batch(db_session, cmd + sqli)
    assert len(alerts) == 2


def test_expired_window_creates_new_alert(db_session, monkeypatch) -> None:
    monkeypatch.setattr(settings, "correlation_window_minutes", 1)
    service = EventService()
    base = datetime(2026, 5, 30, 12, 0, 0, tzinfo=timezone.utc)
    first = _command_event(0, "a; whoami", attack=True)
    first.timestamp = base
    second = _command_event(0, "b; whoami", attack=True)
    second.timestamp = base + timedelta(minutes=5)
    _, alerts = service.ingest_batch(db_session, [first, second])
    assert len(alerts) == 2
