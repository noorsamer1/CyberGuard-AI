"""Tests for failed login burst rule edge cases."""

from __future__ import annotations

from datetime import datetime, timezone

from app.detection.rules.failed_login_rule import FailedLoginBurstRule
from app.models.event import Event


def _event(**kwargs: object) -> Event:
    defaults = {
        "timestamp": datetime(2026, 5, 30, 12, 0, 0, tzinfo=timezone.utc),
        "username": "admin",
        "event_type": "authentication",
        "status": "failed",
        "message": "Failed login to range target",
        "owner_id": 1,
    }
    defaults.update(kwargs)
    return Event(**defaults)


def test_success_login_does_not_match_failed_login(db_session) -> None:
    """Successful logins must not trigger failed_login_burst (message contains 'failures')."""
    rule = FailedLoginBurstRule()
    success = _event(
        status="success",
        severity="high",
        message="Successful login to range target after repeated failures",
    )
    assert rule.evaluate(db_session, success) == []


def test_failed_login_counts_failures_only(db_session) -> None:
    """Rule threshold counts failed attempts, not successful logins in the same window."""
    rule = FailedLoginBurstRule()
    base_ts = datetime(2026, 5, 30, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(5):
        db_session.add(
            _event(
                timestamp=base_ts.replace(second=i),
                status="failed",
                message="Failed login to range target",
            )
        )
    db_session.add(
        _event(
            timestamp=base_ts.replace(second=5),
            status="success",
            message="Successful login to range target after repeated failures",
        )
    )
    db_session.flush()

    sixth_failure = _event(
        timestamp=base_ts.replace(second=6),
        status="failed",
        message="Failed login to range target",
    )
    db_session.add(sixth_failure)
    db_session.flush()

    hits = rule.evaluate(db_session, sixth_failure)
    assert len(hits) == 1
    assert "6 failed login" in hits[0].description
