import random
from datetime import datetime, timedelta, timezone

from app.models.enums import Severity
from app.schemas.event import EventCreate

# RFC 5737 documentation IPs for a coherent demo story
DEMO_BRUTE_IP = "203.0.113.77"
DEMO_SCAN_IP = "203.0.113.88"
DEMO_DENIED_IP = "203.0.113.99"
DEMO_BURST_USER_IP = "203.0.113.66"
DEMO_RATE_IP = "203.0.113.200"
DEMO_INTERNAL_DST = "10.0.50.10"


def generate_synthetic_events(count: int = 50) -> list[EventCreate]:
    """Weighted random traffic (used by API /synthetic)."""
    now = datetime.now(timezone.utc)
    users = ["admin", "jsmith", "svc_backup", "root", "guest"]
    ips_external = [f"203.0.113.{i}" for i in range(1, 40)]
    ips_internal = [f"10.0.{random.randint(0, 5)}.{random.randint(1, 200)}" for _ in range(20)]
    internal_dst = random.choice(ips_internal)
    events: list[EventCreate] = []

    templates = [
        ("login_success", "success", Severity.low, "User login successful"),
        ("login_failed", "failed", Severity.medium, "Invalid password"),
        ("firewall", "denied", Severity.medium, "Connection denied by policy"),
        ("vpn", "success", Severity.low, "VPN session established"),
        ("admin_access", "success", Severity.high, "Privileged command executed"),
        ("port_probe", "open", Severity.high, "Connection attempt to sensitive port"),
    ]

    for _i in range(count):
        ts = now - timedelta(minutes=random.randint(0, 60 * 24 * 7))
        t = random.choices(
            templates,
            weights=[30, 25, 15, 10, 5, 15],
            k=1,
        )[0]
        et, st, base_sev, msg = t
        src = random.choice(ips_external + ips_internal)
        dst = internal_dst
        port = random.choice([22, 80, 443, 3389, 445, 21, random.randint(1024, 65535)])
        if et == "login_failed":
            u = random.choice(users)
            events.append(
                EventCreate(
                    timestamp=ts,
                    source_ip=src,
                    destination_ip=dst,
                    username=u,
                    event_type="authentication",
                    status=st,
                    severity=base_sev,
                    message=msg,
                    protocol="tcp",
                    port=port,
                    raw_log=f"auth failure user={u} src={src}",
                    source_system="idp",
                )
            )
        elif et == "port_probe":
            events.append(
                EventCreate(
                    timestamp=ts,
                    source_ip=src,
                    destination_ip=dst,
                    event_type="network",
                    status=st,
                    severity=Severity.high,
                    message=msg,
                    protocol="tcp",
                    port=port,
                    raw_log=f"probe port={port} src={src}",
                    source_system="ids",
                )
            )
        elif et == "firewall":
            events.append(
                EventCreate(
                    timestamp=ts,
                    source_ip=src,
                    destination_ip=dst,
                    event_type="firewall",
                    status="denied",
                    severity=Severity.medium,
                    message=msg,
                    protocol=random.choice(["tcp", "udp"]),
                    port=port,
                    raw_log=f"DROP {src}->{dst}:{port}",
                    source_system="fw",
                )
            )
        else:
            events.append(
                EventCreate(
                    timestamp=ts,
                    source_ip=src,
                    destination_ip=dst,
                    username=random.choice(users) if et != "vpn" else None,
                    event_type=et,
                    status=st,
                    severity=base_sev,
                    message=msg,
                    protocol="tcp",
                    port=port,
                    raw_log=f"{et} {src}",
                    source_system="siem",
                )
            )

    brute_ip = random.choice(ips_external)
    for j in range(12):
        events.append(
            EventCreate(
                timestamp=now - timedelta(minutes=4) + timedelta(seconds=j),
                source_ip=brute_ip,
                destination_ip=internal_dst,
                username="admin",
                event_type="authentication",
                status="failed",
                severity=Severity.medium,
                message="Invalid password",
                protocol="tcp",
                port=22,
                raw_log="ssh brute",
                source_system="ssh",
            )
        )

    scan_ip = random.choice(ips_external)
    for p in range(20, 45):
        events.append(
            EventCreate(
                timestamp=now - timedelta(minutes=1),
                source_ip=scan_ip,
                destination_ip=internal_dst,
                event_type="network",
                status="attempt",
                severity=Severity.low,
                message="SYN scan",
                protocol="tcp",
                port=p,
                raw_log=f"scan {p}",
                source_system="ids",
            )
        )

    return events


def _sort_by_ts(items: list[EventCreate]) -> list[EventCreate]:
    return sorted(items, key=lambda e: e.timestamp)


def generate_strong_demo_events() -> list[EventCreate]:
    """
    Rich, reproducible SOC demo: background noise plus guaranteed rule hits
    (brute force, port scan, denied spike, failed-login burst, rate anomaly).
    Detection produces incidents at low, medium, high, and critical; standalone
    demo events at T-30m cover every event severity for dashboards.
    Events are returned in chronological order for clean ingest.
    """
    now = datetime.now(timezone.utc)
    events: list[EventCreate] = []
    users = ["admin", "jsmith", "svc_backup", "root", "guest"]
    ips_benign = [f"198.51.100.{i}" for i in range(1, 30)]

    # --- Background: spread over 7 days (no recent overlap with scripted scenarios) ---
    for _ in range(55):
        ts = now - timedelta(
            hours=random.randint(6, 24 * 7),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        if ts > now - timedelta(hours=3):
            ts = now - timedelta(hours=random.randint(4, 24 * 7))
        src = random.choice(ips_benign)
        port = random.choice([443, 80, 22, 3389, 53, random.randint(40000, 50000)])
        roll = random.random()
        if roll < 0.35:
            events.append(
                EventCreate(
                    timestamp=ts,
                    source_ip=src,
                    destination_ip=DEMO_INTERNAL_DST,
                    username=random.choice(users),
                    event_type="authentication",
                    status="success",
                    severity=Severity.low,
                    message="User login successful",
                    protocol="tcp",
                    port=port,
                    raw_log=f"ok user={users[0]}",
                    source_system="idp",
                )
            )
        elif roll < 0.55:
            events.append(
                EventCreate(
                    timestamp=ts,
                    source_ip=src,
                    destination_ip=DEMO_INTERNAL_DST,
                    event_type="firewall",
                    status="allowed",
                    severity=Severity.low,
                    message="Connection allowed",
                    protocol="tcp",
                    port=port,
                    raw_log="ACCEPT",
                    source_system="fw",
                )
            )
        elif roll < 0.75:
            events.append(
                EventCreate(
                    timestamp=ts,
                    source_ip=src,
                    destination_ip=DEMO_INTERNAL_DST,
                    event_type="network",
                    status="info",
                    severity=Severity.low,
                    message="Flow observed",
                    protocol="tcp",
                    port=port,
                    raw_log="netflow",
                    source_system="sensor",
                )
            )
        else:
            events.append(
                EventCreate(
                    timestamp=ts,
                    source_ip=src,
                    destination_ip=DEMO_INTERNAL_DST,
                    username=None,
                    event_type="vpn",
                    status="success",
                    severity=Severity.low,
                    message="VPN session established",
                    protocol="udp",
                    port=1194,
                    raw_log="vpn up",
                    source_system="vpn",
                )
            )

    # --- T-95 to T-88 min: denied access spike (≥20 in 5 min) ---
    base_denied = now - timedelta(minutes=92)
    for i in range(24):
        events.append(
            EventCreate(
                timestamp=base_denied + timedelta(seconds=i * 8),
                source_ip=DEMO_DENIED_IP,
                destination_ip=DEMO_INTERNAL_DST,
                event_type="firewall",
                status="denied",
                severity=Severity.low,
                message="Connection denied by policy",
                protocol="tcp",
                port=random.choice([22, 445, 3389, 1433, 5432]),
                raw_log=f"DROP {DEMO_DENIED_IP}->{DEMO_INTERNAL_DST}",
                source_system="fw",
            )
        )

    # --- T-84 to T-82 min: port scan (≥15 distinct ports in 2 min) ---
    scan_start = now - timedelta(minutes=83)
    for idx, port in enumerate(range(3000, 3026)):
        events.append(
            EventCreate(
                timestamp=scan_start + timedelta(seconds=idx * 4),
                source_ip=DEMO_SCAN_IP,
                destination_ip=DEMO_INTERNAL_DST,
                event_type="network",
                status="attempt",
                severity=Severity.medium,
                message="SYN scan",
                protocol="tcp",
                port=port,
                raw_log=f"scan dst_port={port}",
                source_system="ids",
            )
        )

    # --- T-72 to T-69 min: brute force (≥10 auth failures in 5 min) ---
    brute_start = now - timedelta(minutes=71)
    for j in range(14):
        events.append(
            EventCreate(
                timestamp=brute_start + timedelta(seconds=j * 12),
                source_ip=DEMO_BRUTE_IP,
                destination_ip=DEMO_INTERNAL_DST,
                username="admin",
                event_type="authentication",
                status="failed",
                severity=Severity.medium,
                message="Invalid password",
                protocol="tcp",
                port=22,
                raw_log="sshd: Failed password for admin",
                source_system="ssh",
            )
        )

    # --- T-62 to T-60 min: failed-login burst by username (≥6 in 5 min) ---
    burst_start = now - timedelta(minutes=61)
    for j in range(8):
        events.append(
            EventCreate(
                timestamp=burst_start + timedelta(seconds=j * 15),
                source_ip=DEMO_BURST_USER_IP,
                destination_ip=DEMO_INTERNAL_DST,
                username="jsmith",
                event_type="authentication",
                status="failed",
                severity=Severity.medium,
                message="Invalid password",
                protocol="tcp",
                port=443,
                raw_log="oauth failed jsmith",
                source_system="idp",
            )
        )

    # --- T-45 min: post-incident “normal” + analyst context ---
    calm = now - timedelta(minutes=45)
    events.append(
        EventCreate(
            timestamp=calm,
            source_ip="10.0.10.5",
            destination_ip=DEMO_INTERNAL_DST,
            username="soc_operator",
            event_type="admin_access",
            status="success",
            severity=Severity.low,
            message="Ticket updated — triage in progress",
            protocol="tcp",
            port=443,
            raw_log="itsm api",
            source_system="itsm",
        )
    )

    # --- T-12 min: extreme rate anomaly (≥80 events in 1 min) — critical alert ---
    rate_start = now - timedelta(minutes=12)
    for k in range(85):
        events.append(
            EventCreate(
                timestamp=rate_start + timedelta(milliseconds=650 * k),
                source_ip=DEMO_RATE_IP,
                destination_ip=DEMO_INTERNAL_DST,
                event_type="generic",
                status="info",
                severity=Severity.low,
                message="Automated health ping",
                protocol="tcp",
                port=8080,
                raw_log=f"probe k={k}",
                source_system="synthetic",
            )
        )

    # --- Recent benign noise (last 25 min) ---
    for _ in range(25):
        ts = now - timedelta(minutes=random.randint(0, 25), seconds=random.randint(0, 59))
        events.append(
            EventCreate(
                timestamp=ts,
                source_ip=random.choice(ips_benign),
                destination_ip=DEMO_INTERNAL_DST,
                event_type="authentication",
                status="success",
                severity=Severity.low,
                message="User login successful",
                protocol="tcp",
                port=443,
                raw_log="ok",
                source_system="idp",
            )
        )

    # --- T-30 min: one row per severity for dashboard / training (no detection rule) ---
    mix = now - timedelta(minutes=30)
    events.extend(
        [
            EventCreate(
                timestamp=mix,
                source_ip="203.0.113.10",
                destination_ip=DEMO_INTERNAL_DST,
                username=None,
                event_type="endpoint",
                status="info",
                severity=Severity.low,
                message="Patch deferred — maintenance window (demo)",
                protocol="tcp",
                port=443,
                raw_log="demo_severity_mix low",
                source_system="mdm",
            ),
            EventCreate(
                timestamp=mix + timedelta(seconds=5),
                source_ip="203.0.113.11",
                destination_ip=DEMO_INTERNAL_DST,
                username="contractor1",
                event_type="dlp",
                status="warning",
                severity=Severity.medium,
                message="Sensitive file copy attempt (demo)",
                protocol="tcp",
                port=445,
                raw_log="demo_severity_mix medium",
                source_system="dlp",
            ),
            EventCreate(
                timestamp=mix + timedelta(seconds=10),
                source_ip="203.0.113.12",
                destination_ip=DEMO_INTERNAL_DST,
                username=None,
                event_type="network",
                status="blocked",
                severity=Severity.high,
                message="C2-like beacon pattern (demo)",
                protocol="tcp",
                port=8443,
                raw_log="demo_severity_mix high",
                source_system="ids",
            ),
            EventCreate(
                timestamp=mix + timedelta(seconds=15),
                source_ip="203.0.113.13",
                destination_ip=DEMO_INTERNAL_DST,
                username=None,
                event_type="malware",
                status="blocked",
                severity=Severity.critical,
                message="Quarantined ransomware signature (demo)",
                protocol="tcp",
                port=443,
                raw_log="demo_severity_mix critical",
                source_system="edr",
            ),
        ]
    )

    return _sort_by_ts(events)


def strong_demo_legend() -> str:
    return (
        "Demo storyline (RFC 5737 TEST-NET-3 IPs):\n"
        f"  - Denied spike:   {DEMO_DENIED_IP}  (rule: denied_access_spike, incident severity: low)\n"
        f"  - Port scan:      {DEMO_SCAN_IP}  (rule: port_scan, incident severity: medium)\n"
        f"  - Brute-force:    {DEMO_BRUTE_IP}  (rule: brute_force, incident severity: high)\n"
        f"  - Login burst:    user jsmith from {DEMO_BURST_USER_IP}  (rule: failed_login_burst, incident severity: medium)\n"
        f"  - Rate anomaly:   {DEMO_RATE_IP}  (rule: event_rate_anomaly, incident severity: critical)\n"
        "  - Severity mix:   203.0.113.10–13 at T-30m (standalone demo events: low→critical)\n"
    )
