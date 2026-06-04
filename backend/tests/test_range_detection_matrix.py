"""Tests for range scenario -> detection correctness matrix."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.detection.engine import DetectionEngine
from app.services.event_service import EventService
from app.services.range_service import RANGE_SCENARIOS, logs_to_events
from tests.fixtures.range_logs import EXPECTED_SEVERITIES, SCENARIO_LOG_BUILDERS


@pytest.fixture(autouse=True)
def disable_correlation(monkeypatch):
    monkeypatch.setattr(settings, "correlation_enabled", False)


def _collect_hits(db_session, scenario_id: str) -> dict[str, tuple[str, str]]:
    logs = SCENARIO_LOG_BUILDERS[scenario_id]()
    events_payload = logs_to_events(logs)
    service = EventService()
    _, alerts = service.ingest_batch(db_session, events_payload)
    hits: dict[str, tuple[str, str]] = {}
    for alert in alerts:
        hits[alert.rule_name] = (alert.severity.value, alert.reasoning or "")
    return hits


@pytest.mark.parametrize("scenario_id", list(RANGE_SCENARIOS.keys()))
def test_scenario_expected_detections(db_session, scenario_id: str) -> None:
    scenario = RANGE_SCENARIOS[scenario_id]
    hits = _collect_hits(db_session, scenario_id)
    assert set(hits.keys()) == set(scenario.expected_detections)
    for rule_name in scenario.expected_detections:
        expected_sev = EXPECTED_SEVERITIES[rule_name]
        actual_sev, reasoning = hits[rule_name]
        assert actual_sev == expected_sev
        assert "Evidence:" in reasoning


def test_sql_injection_reasoning_references_telemetry(db_session) -> None:
    hits = _collect_hits(db_session, "range_sql_injection")
    reasoning = hits["sql_injection_attempt"][1].lower()
    assert "sql" in reasoning or "injection" in reasoning or "search" in reasoning


def test_engine_loads_all_rules() -> None:
    engine = DetectionEngine()
    assert len(engine.rules) >= 10
