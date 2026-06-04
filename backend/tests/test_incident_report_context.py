"""Tests for deterministic incident report context."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.models.enums import IncidentStatus
from app.models.incident import Incident
from app.services.event_service import EventService
from app.services.incident_report_context import build_incident_report_context, format_duration
from app.services.range_service import logs_to_events
from tests.fixtures.range_logs import _log


@pytest.fixture()
def enable_correlation(monkeypatch):
    monkeypatch.setattr(settings, "correlation_enabled", True)


def _make_incident(db_session) -> Incident:
    """Create an incident with multiple correlated events attached."""
    service = EventService()
    base = datetime(2026, 5, 30, 12, 0, 0, tzinfo=timezone.utc)
    logs = [
        _log(
            timestamp=(base + timedelta(seconds=i)).isoformat(),
            event_type="web_attack",
            status="blocked",
            severity="high",
            message=f"Command injection payload blocked: payload-{i}; whoami",
            raw_log=f"POST /exec payload=payload-{i}; whoami",
            metadata={"attack": "command_injection", "payload": f"payload-{i}; whoami"},
        )
        for i in range(3)
    ]
    _, alerts = service.ingest_batch(db_session, logs_to_events(logs))
    assert alerts
    incident = db_session.get(Incident, alerts[0].incident_id)
    assert incident is not None
    db_session.refresh(incident)
    return incident


def test_report_context_includes_mtta_and_severity_breakdown(
    db_session, enable_correlation
) -> None:
    incident = _make_incident(db_session)
    ctx = build_incident_report_context(db_session, incident)
    assert ctx.event_count >= 2
    assert "high" in ctx.severity_breakdown
    assert ctx.mtta_seconds is not None
    assert ctx.mtta_seconds >= 0


def test_format_duration_human_readable() -> None:
    assert format_duration(45) == "45s"
    assert format_duration(120) == "2.0m"
    assert format_duration(None) == "N/A"


def test_remediation_progress_reflects_status(db_session, enable_correlation) -> None:
    incident = _make_incident(db_session)
    incident.status = IncidentStatus.investigating
    ctx = build_incident_report_context(db_session, incident)
    assert "investigation" in ctx.remediation_progress.lower()
