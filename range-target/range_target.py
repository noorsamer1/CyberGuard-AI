from __future__ import annotations

import json
import os
import socket
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse


HOST = "0.0.0.0"
HTTP_PORT = 8088
DUMMY_PORTS = list(range(8089, 8104))
SECRET = os.getenv("RANGE_SHARED_SECRET", "dev-range-secret-change-me")

_lock = threading.Lock()
_logs: list[dict[str, Any]] = []
_dummy_files = {
    "public/readme.txt": "Welcome to the CyberGuard local range target.",
    "reports/q4-summary.txt": "Dummy quarterly report for safe demo use.",
    "sensitive/customer_database_export.csv": "id,name,email\n1,Ada,ada@example.test\n",
    "sensitive/hr_salary_q4.xlsx": "dummy binary placeholder",
}
_renamed_files: set[str] = set()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record(
    *,
    event_type: str,
    status: str,
    severity: str,
    message: str,
    source_ip: str,
    username: str | None = None,
    port: int | None = HTTP_PORT,
    raw_log: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    row = {
        "timestamp": _now(),
        "source_ip": source_ip or "127.0.0.1",
        "destination_ip": "range-target",
        "username": username,
        "event_type": event_type,
        "status": status,
        "severity": severity,
        "message": message,
        "protocol": "tcp",
        "port": port,
        "raw_log": raw_log or message,
        "source_system": "range-target",
        "metadata": metadata or {},
    }
    with _lock:
        _logs.append(row)


def _reset_state() -> None:
    global _renamed_files
    with _lock:
        _logs.clear()
        _renamed_files = set()


def _drain_logs() -> list[dict[str, Any]]:
    with _lock:
        out = list(_logs)
        _logs.clear()
    return out


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or 0)
    raw = handler.rfile.read(length) if length else b"{}"
    if not raw:
        return {}
    content_type = handler.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
    parsed = parse_qs(raw.decode("utf-8"), keep_blank_values=True)
    return {k: v[-1] if v else "" for k, v in parsed.items()}


def _send(handler: BaseHTTPRequestHandler, code: int, body: dict[str, Any]) -> None:
    raw = json.dumps(body).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", _CORS_ALLOW_HEADERS)
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _authorized(handler: BaseHTTPRequestHandler) -> bool:
    return handler.headers.get("X-Range-Secret") == SECRET


def _looks_like_ip(value: str) -> bool:
    """Basic validation for client-supplied origin IP (IPv4 or IPv6)."""
    if not value or len(value) > 45:
        return False
    if value.count(".") == 3:
        parts = value.split(".")
        return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)
    if ":" in value:
        return all(c in "0123456789abcdefABCDEF:" for c in value)
    return False


def _effective_source_ip(handler: BaseHTTPRequestHandler) -> str:
    """Prefer device-origin IP from browser lab launches over Docker bridge address."""
    override = (handler.headers.get("X-Range-Client-Ip") or "").strip()
    if override and _looks_like_ip(override):
        return override
    return handler.client_address[0] or "127.0.0.1"


_CORS_ALLOW_HEADERS = "Content-Type, X-Range-Secret, X-Range-Client-Ip"


class RangeHandler(BaseHTTPRequestHandler):
    server_version = "CyberGuardRangeTarget/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", _CORS_ALLOW_HEADERS)
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query, keep_blank_values=True)
        source_ip = _effective_source_ip(self)

        if parsed.path == "/health":
            _send(self, 200, {"status": "ok", "service": "cyberguard-range-target"})
            return

        if parsed.path == "/_range/logs":
            if not _authorized(self):
                _send(self, 401, {"message": "unauthorized"})
                return
            _send(self, 200, {"logs": _drain_logs()})
            return

        if parsed.path == "/search":
            term = (query.get("q") or [""])[0]
            suspicious = any(x in term.lower() for x in ["' or", " union ", "--", "/*", "drop table"])
            if suspicious:
                _record(
                    event_type="web_attack",
                    status="blocked",
                    severity="high",
                    message=f"SQL injection attempt against search query: {term[:120]}",
                    source_ip=source_ip,
                    raw_log=f"GET /search?q={term}",
                    metadata={"attack": "sql_injection", "endpoint": "/search"},
                )
                _send(self, 200, {"results": ["all dummy rows returned by intentionally vulnerable search"]})
                return
            _record(
                event_type="web",
                status="ok",
                severity="low",
                message=f"Normal search query: {term[:120]}",
                source_ip=source_ip,
                raw_log=f"GET /search?q={term}",
            )
            _send(self, 200, {"results": ["public result"]})
            return

        if parsed.path == "/files":
            requested = (query.get("path") or ["public/readme.txt"])[0]
            if ".." in requested or requested.startswith("/"):
                _record(
                    event_type="web_attack",
                    status="blocked",
                    severity="high",
                    message=f"Path traversal attempt for path: {requested[:160]}",
                    source_ip=source_ip,
                    raw_log=f"GET /files?path={requested}",
                    metadata={"attack": "path_traversal", "endpoint": "/files"},
                )
                _send(self, 403, {"message": "blocked by range guard"})
                return
            content = _dummy_files.get(requested, "not found")
            _record(
                event_type="file_access",
                status="ok",
                severity="low",
                message=f"Dummy file read: {requested}",
                source_ip=source_ip,
                raw_log=f"GET /files?path={requested}",
            )
            _send(self, 200, {"path": requested, "content": content})
            return

        _send(self, 404, {"message": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        source_ip = _effective_source_ip(self)

        if parsed.path == "/_range/reset":
            if not _authorized(self):
                _send(self, 401, {"message": "unauthorized"})
                return
            _reset_state()
            _send(self, 200, {"status": "reset"})
            return

        if parsed.path == "/login":
            body = _read_json(self)
            username = str(body.get("username", ""))
            password = str(body.get("password", ""))
            ok = username == "admin" and password == "CyberGuard!2026"
            _record(
                event_type="authentication",
                status="success" if ok else "failed",
                severity="high" if ok else "medium",
                message=(
                    "Successful login to range target after repeated failures"
                    if ok
                    else "Failed login to range target"
                ),
                source_ip=source_ip,
                username=username,
                raw_log=f"POST /login user={username} status={'success' if ok else 'failed'}",
                metadata={"endpoint": "/login"},
            )
            _send(self, 200 if ok else 401, {"authenticated": ok})
            return

        if parsed.path == "/exfil":
            body = _read_json(self)
            filename = str(body.get("file", "sensitive/customer_database_export.csv"))
            size_mb = int(body.get("size_mb", 75) or 75)
            _record(
                event_type="dlp",
                status="warning",
                severity="high",
                message=f"Sensitive file access: {filename}",
                source_ip=source_ip,
                username=str(body.get("username", "contractor1")),
                port=HTTP_PORT,
                raw_log=f"DLP WARN file_access file={filename}",
                metadata={"attack": "exfiltration", "file": filename},
            )
            _record(
                event_type="network",
                status="allowed",
                severity="high",
                message="Large outbound data transfer to local range collector",
                source_ip=source_ip,
                username=str(body.get("username", "contractor1")),
                port=HTTP_PORT,
                raw_log=f"netflow local_range bytes={size_mb}MB file={filename}",
                metadata={"attack": "exfiltration", "size_mb": size_mb},
            )
            _send(self, 200, {"status": "staged", "file": filename, "size_mb": size_mb})
            return

        if parsed.path == "/ransomware/simulate":
            renamed: list[str] = []
            for name in list(_dummy_files.keys()):
                if name.startswith("sensitive/") and name not in _renamed_files:
                    _renamed_files.add(name)
                    renamed.append(f"{name}.locked")
            _record(
                event_type="endpoint",
                status="warning",
                severity="critical",
                message=f"Range ransomware simulation renamed {len(renamed)} dummy files",
                source_ip=source_ip,
                port=HTTP_PORT,
                raw_log=f"ransomware_simulation renamed={len(renamed)} extension=.locked",
                metadata={"attack": "ransomware_simulation", "renamed": renamed},
            )
            _record(
                event_type="malware",
                status="blocked",
                severity="critical",
                message="Ransomware simulation payload blocked inside disposable range target",
                source_ip=source_ip,
                port=HTTP_PORT,
                raw_log="EDR BLOCK local_range_ransomware_simulation",
                metadata={"attack": "ransomware_simulation"},
            )
            _send(self, 200, {"renamed": renamed, "safe": True})
            return

        if parsed.path == "/dns/query":
            body = _read_json(self)
            query = str(body.get("query", "healthcheck.local"))
            lowered = query.lower()
            suspicious = len(query) > 32 or any(
                marker in lowered for marker in ("=", "exfil", "credential", "chunk")
            )
            metadata: dict[str, Any] = {"query": query}
            if suspicious:
                metadata["attack"] = "dns_tunneling"
            _record(
                event_type="dns",
                status="warning" if suspicious else "ok",
                severity="high" if suspicious else "low",
                message=(
                    f"Suspicious DNS query pattern observed: {query[:180]}"
                    if suspicious
                    else f"Normal DNS lookup: {query[:180]}"
                ),
                source_ip=source_ip,
                port=53,
                raw_log=f"dns_query qname={query}",
                metadata=metadata,
            )
            _send(self, 200, {"resolved": True, "query": query, "suspicious": suspicious})
            return

        if parsed.path == "/auth/spray":
            body = _read_json(self)
            username = str(body.get("username", "unknown"))
            password = str(body.get("password", ""))
            ok = username == "admin" and password == "CyberGuard!2026"
            _record(
                event_type="authentication",
                status="success" if ok else "failed",
                severity="high" if not ok else "medium",
                message=(
                    "Password spray attempt succeeded on privileged account"
                    if ok
                    else "Password spray attempt failed"
                ),
                source_ip=source_ip,
                username=username,
                port=HTTP_PORT,
                raw_log=f"POST /auth/spray user={username} status={'success' if ok else 'failed'}",
                metadata={"attack": "password_spray", "username": username},
            )
            _send(self, 200 if ok else 401, {"authenticated": ok, "username": username})
            return

        if parsed.path == "/exec":
            body = _read_json(self)
            payload = str(body.get("input", ""))
            lowered = payload.lower()
            suspicious = any(token in lowered for token in (";", "&&", "|", "$(", "`", "whoami", "id"))
            metadata_exec: dict[str, Any] = {"payload": payload}
            if suspicious:
                metadata_exec["attack"] = "command_injection"
            _record(
                event_type="web_attack" if suspicious else "web",
                status="blocked" if suspicious else "ok",
                severity="high" if suspicious else "low",
                message=(
                    f"Command injection payload blocked: {payload[:180]}"
                    if suspicious
                    else f"Safe command input accepted: {payload[:180]}"
                ),
                source_ip=source_ip,
                port=HTTP_PORT,
                raw_log=f"POST /exec payload={payload}",
                metadata=metadata_exec,
            )
            _send(self, 200, {"accepted": not suspicious, "blocked": suspicious})
            return

        if parsed.path == "/priv-esc":
            body = _read_json(self)
            username = str(body.get("username", "analyst"))
            action = str(body.get("action", "sudo -l"))
            _record(
                event_type="admin_access",
                status="warning",
                severity="critical",
                message=f"Privilege escalation behavior detected for {username}: {action[:160]}",
                source_ip=source_ip,
                username=username,
                port=HTTP_PORT,
                raw_log=f"POST /priv-esc user={username} action={action}",
                metadata={"attack": "privilege_escalation", "action": action},
            )
            _send(self, 200, {"recorded": True, "username": username, "action": action})
            return

        _send(self, 404, {"message": "not found"})


def _dummy_listener(port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, port))
    sock.listen(5)
    while True:
        conn, addr = sock.accept()
        _record(
            event_type="network",
            status="attempt",
            severity="low",
            message=f"TCP probe observed on local range port {port}",
            source_ip=addr[0],
            port=port,
            raw_log=f"tcp_probe port={port} src={addr[0]}",
            metadata={"attack": "port_scan", "port": port},
        )
        try:
            conn.sendall(b"CyberGuard local range dummy service\r\n")
        finally:
            conn.close()


def main() -> None:
    for port in DUMMY_PORTS:
        thread = threading.Thread(target=_dummy_listener, args=(port,), daemon=True)
        thread.start()
    server = ThreadingHTTPServer((HOST, HTTP_PORT), RangeHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
