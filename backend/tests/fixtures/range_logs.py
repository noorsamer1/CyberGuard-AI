"""Canonical range log fixtures matching range_target.py telemetry."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

BASE_TS = datetime(2026, 5, 30, 12, 0, 0, tzinfo=timezone.utc)
SOURCE_IP = "127.0.0.1"


def _ts(offset_seconds: int) -> str:
    return (BASE_TS + timedelta(seconds=offset_seconds)).isoformat()


def _log(**kwargs: Any) -> dict[str, Any]:
    row = {
        "timestamp": kwargs.pop("timestamp", _ts(0)),
        "source_ip": kwargs.pop("source_ip", SOURCE_IP),
        "destination_ip": "range-target",
        "username": kwargs.pop("username", None),
        "event_type": kwargs.pop("event_type", "range_event"),
        "status": kwargs.pop("status", "ok"),
        "severity": kwargs.pop("severity", "low"),
        "message": kwargs.pop("message", ""),
        "protocol": kwargs.pop("protocol", "tcp"),
        "port": kwargs.pop("port", 8088),
        "raw_log": kwargs.pop("raw_log", kwargs.get("message", "")),
        "source_system": "range-target",
        "metadata": kwargs.pop("metadata", {}),
    }
    row.update(kwargs)
    return row


def brute_force_logs() -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    for i in range(10):
        logs.append(
            _log(
                timestamp=_ts(i),
                event_type="authentication",
                status="failed",
                severity="medium",
                username="admin",
                message="Failed login to range target",
                raw_log=f"POST /login user=admin status=failed attempt={i}",
                metadata={"endpoint": "/login"},
            )
        )
    logs.append(
        _log(
            timestamp=_ts(10),
            event_type="authentication",
            status="success",
            severity="high",
            username="admin",
            message="Successful login to range target after repeated failures",
            raw_log="POST /login user=admin status=success",
            metadata={"endpoint": "/login"},
        )
    )
    return logs


def port_scan_logs() -> list[dict[str, Any]]:
    return [
        _log(
            timestamp=_ts(i),
            event_type="network",
            status="attempt",
            severity="low",
            port=8088 + i,
            message=f"TCP probe observed on local range port {8088 + i}",
            raw_log=f"tcp_probe port={8088 + i} src={SOURCE_IP}",
            metadata={"attack": "port_scan", "port": 8088 + i},
        )
        for i in range(16)
    ]


def sql_injection_logs() -> list[dict[str, Any]]:
    return [
        _log(
            timestamp=_ts(0),
            event_type="web",
            status="ok",
            message="Normal search query: demo",
            raw_log="GET /search?q=demo",
        ),
        _log(
            timestamp=_ts(1),
            event_type="web_attack",
            status="blocked",
            severity="high",
            message="SQL injection attempt against search query: ' OR '1'='1'--",
            raw_log="GET /search?q=' OR '1'='1'--",
            metadata={"attack": "sql_injection", "endpoint": "/search"},
        ),
    ]


def path_traversal_logs() -> list[dict[str, Any]]:
    return [
        _log(
            timestamp=_ts(0),
            event_type="web_attack",
            status="blocked",
            severity="high",
            message="Path traversal attempt for path: ../../etc/passwd",
            raw_log="GET /files?path=../../etc/passwd",
            metadata={"attack": "path_traversal", "endpoint": "/files"},
        )
    ]


def exfiltration_logs() -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    for i in range(3):
        logs.extend(
            [
                _log(
                    timestamp=_ts(i * 2),
                    event_type="dlp",
                    status="warning",
                    severity="high",
                    username="contractor1",
                    message="Sensitive file access: sensitive/customer_database_export.csv",
                    raw_log="DLP WARN file_access file=sensitive/customer_database_export.csv",
                    metadata={"attack": "exfiltration", "file": "sensitive/customer_database_export.csv"},
                ),
                _log(
                    timestamp=_ts(i * 2 + 1),
                    event_type="network",
                    status="allowed",
                    severity="high",
                    username="contractor1",
                    message="Large outbound data transfer to local range collector",
                    raw_log=f"netflow local_range bytes={80 + i * 20}MB file=sensitive/customer_database_export.csv",
                    metadata={"attack": "exfiltration", "size_mb": 80 + i * 20},
                ),
            ]
        )
    return logs


def ransomware_logs() -> list[dict[str, Any]]:
    return [
        _log(
            timestamp=_ts(0),
            event_type="endpoint",
            status="warning",
            severity="critical",
            message="Range ransomware simulation renamed 2 dummy files",
            raw_log="ransomware_simulation renamed=2 extension=.locked",
            metadata={"attack": "ransomware_simulation", "renamed": ["a.locked", "b.locked"]},
        ),
        _log(
            timestamp=_ts(1),
            event_type="malware",
            status="blocked",
            severity="critical",
            message="Ransomware simulation payload blocked inside disposable range target",
            raw_log="EDR BLOCK local_range_ransomware_simulation",
            metadata={"attack": "ransomware_simulation"},
        ),
    ]


def dns_tunneling_logs() -> list[dict[str, Any]]:
    logs = [
        _log(
            timestamp=_ts(0),
            event_type="dns",
            status="ok",
            severity="low",
            port=53,
            message="Normal DNS lookup: healthcheck.local",
            raw_log="dns_query qname=healthcheck.local",
            metadata={"query": "healthcheck.local"},
        )
    ]
    queries = [
        "c2VjcmV0LXNlZ21lbnQtMDE=.corp.lab.local",
        "Y3JlZGVudGlhbD1hZG1pbjpQYXNzMTIz.corp.lab.local",
        "ZmlsZT1jdXN0b21lcnMuY3N2JmNodW5rPTM=.corp.lab.local",
        "ZXhmaWw9cGF5cm9sbC1kYXRhJmNoZWNrPTQ=.corp.lab.local",
    ]
    for i, query in enumerate(queries, start=1):
        logs.append(
            _log(
                timestamp=_ts(i),
                event_type="dns",
                status="warning",
                severity="high",
                port=53,
                message=f"Suspicious DNS query pattern observed: {query}",
                raw_log=f"dns_query qname={query}",
                metadata={"attack": "dns_tunneling", "query": query},
            )
        )
    return logs


def password_spray_logs() -> list[dict[str, Any]]:
    usernames = [
        "admin",
        "it.support",
        "finance.manager",
        "ceo.assistant",
        "ops.lead",
        "analyst",
        "helpdesk",
        "intern",
        "hr.manager",
        "developer",
    ]
    return [
        _log(
            timestamp=_ts(i),
            event_type="authentication",
            status="failed",
            severity="high",
            username=username,
            message="Password spray attempt failed",
            raw_log=f"POST /auth/spray user={username} status=failed",
            metadata={"attack": "password_spray", "username": username},
        )
        for i, username in enumerate(usernames)
    ]


def command_injection_logs() -> list[dict[str, Any]]:
    return [
        _log(
            timestamp=_ts(0),
            event_type="web",
            status="ok",
            severity="low",
            message="Safe command input accepted: report.csv",
            raw_log="POST /exec payload=report.csv",
            metadata={"payload": "report.csv"},
        ),
        _log(
            timestamp=_ts(1),
            event_type="web_attack",
            status="blocked",
            severity="high",
            message="Command injection payload blocked: report.csv; whoami",
            raw_log="POST /exec payload=report.csv; whoami",
            metadata={"attack": "command_injection", "payload": "report.csv; whoami"},
        ),
    ]


def privilege_escalation_logs() -> list[dict[str, Any]]:
    return [
        _log(
            timestamp=_ts(0),
            event_type="admin_access",
            status="warning",
            severity="critical",
            username="analyst",
            message="Privilege escalation behavior detected for analyst: sudo su -",
            raw_log="POST /priv-esc user=analyst action=sudo su -",
            metadata={"attack": "privilege_escalation", "action": "sudo su -"},
        )
    ]


SCENARIO_LOG_BUILDERS = {
    "range_brute_force": brute_force_logs,
    "range_port_scan": port_scan_logs,
    "range_sql_injection": sql_injection_logs,
    "range_path_traversal": path_traversal_logs,
    "range_exfiltration": exfiltration_logs,
    "range_ransomware": ransomware_logs,
    "range_dns_tunneling": dns_tunneling_logs,
    "range_password_spray": password_spray_logs,
    "range_command_injection": command_injection_logs,
    "range_privilege_escalation": privilege_escalation_logs,
}

EXPECTED_SEVERITIES = {
    "brute_force": "high",
    "failed_login_burst": "medium",
    "port_scan": "medium",
    "sql_injection_attempt": "high",
    "path_traversal_attempt": "high",
    "data_exfiltration": "critical",
    "ransomware_simulation": "critical",
    "dns_tunneling_suspected": "high",
    "password_spray": "high",
    "command_injection_attempt": "high",
    "privilege_escalation_suspected": "critical",
}
