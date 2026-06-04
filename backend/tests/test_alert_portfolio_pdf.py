"""Verify alert portfolio PDF includes chart images."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from app.models.enums import AlertStatus, Severity
from app.services.alert_portfolio_service import build_alert_portfolio_context
from app.services.report_service import build_alerts_portfolio_pdf


def _mock_alert(
    alert_id: int,
    *,
    severity: Severity,
    status: AlertStatus,
    rule: str,
    attack: str,
    source_ip: str,
    created_at: datetime,
) -> SimpleNamespace:
    event = SimpleNamespace(source_ip=source_ip)
    return SimpleNamespace(
        id=alert_id,
        severity=severity,
        status=status,
        rule_name=rule,
        attack_type=attack,
        title=f"Alert {alert_id}",
        event_count=2,
        created_at=created_at,
        event=event,
    )


def test_alert_portfolio_pdf_contains_chart_images(tmp_path: Path) -> None:
    """Generated portfolio PDF must embed PNG chart objects."""
    alerts = [
        _mock_alert(
            1,
            severity=Severity.high,
            status=AlertStatus.new,
            rule="failed_login",
            attack="brute_force",
            source_ip="192.168.1.50",
            created_at=datetime(2026, 5, 30, 10, 0, tzinfo=timezone.utc),
        ),
        _mock_alert(
            2,
            severity=Severity.medium,
            status=AlertStatus.acknowledged,
            rule="port_scan",
            attack="port_scan",
            source_ip="10.0.0.8",
            created_at=datetime(2026, 6, 4, 14, 30, tzinfo=timezone.utc),
        ),
        _mock_alert(
            3,
            severity=Severity.critical,
            status=AlertStatus.new,
            rule="sql_injection",
            attack="sql_injection",
            source_ip="192.168.1.50",
            created_at=datetime(2026, 6, 4, 15, 0, tzinfo=timezone.utc),
        ),
    ]
    ctx = build_alert_portfolio_context(alerts)
    assert ctx["executive_summary"]
    assert ctx["timeline_buckets"]

    out = tmp_path / "test-alerts.pdf"
    build_alerts_portfolio_pdf(ctx, out)
    assert out.exists()
    raw = out.read_bytes()
    assert b"/Image" in raw or b"/XObject" in raw
    assert len(raw) > 8000
