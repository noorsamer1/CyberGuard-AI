"""Verify range runner exposes real attack commands aligned with HTTP probes."""

from __future__ import annotations

import pytest

from app.services.range_service import (
    RANGE_SCENARIOS,
    RangeAttackRunner,
    preview_execution_commands,
)


@pytest.mark.parametrize("scenario_id", list(RANGE_SCENARIOS.keys()))
def test_preview_commands_include_reset_attacks_and_drain(scenario_id: str) -> None:
    runner = RangeAttackRunner()
    commands = preview_execution_commands(
        scenario_id,
        runner.target_url,
        runner.public_url,
    )
    assert len(commands) >= 3
    assert "/_range/reset" in commands[0]
    assert "/_range/logs" in commands[-1]
    attack_lines = commands[1:-1]
    assert attack_lines
    for line in attack_lines:
        assert line.startswith("curl") or line.startswith("python3")


@pytest.mark.parametrize("scenario_id", list(RANGE_SCENARIOS.keys()))
def test_preview_attack_count_by_scenario(scenario_id: str) -> None:
    runner = RangeAttackRunner()
    commands = preview_execution_commands(
        scenario_id,
        runner.target_url,
        runner.public_url,
    )
    expected_attacks = {
        "range_brute_force": 11,
        "range_sql_injection": 3,
        "range_path_traversal": 3,
        "range_exfiltration": 3,
        "range_ransomware": 1,
        "range_port_scan": 16,
        "range_dns_tunneling": 5,
        "range_password_spray": 10,
        "range_command_injection": 5,
        "range_privilege_escalation": 4,
    }
    assert len(commands) - 2 == expected_attacks[scenario_id]


def test_device_port_scan_uses_http_probes() -> None:
    runner = RangeAttackRunner()
    commands = preview_execution_commands(
        "range_port_scan",
        runner.target_url,
        runner.public_url,
        client_ip="192.168.1.50",
    )
    attack_lines = commands[1:-1]
    assert all("curl" in line and "/health" in line for line in attack_lines)
    assert all("X-Range-Client-Ip" in line for line in attack_lines)
