import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.models.enums import Severity
from app.schemas.event import EventCreate

_INTERNAL_DST = "10.0.50.10"
_IP_BRUTE = "203.0.113.150"
_IP_STUFFING = "203.0.113.151"
_IP_SCANNER = "203.0.113.152"
_IP_RANSOM_C2 = "203.0.113.153"
_IP_EXFIL = "203.0.113.154"
_IP_APT_1 = "203.0.113.155"
_IP_APT_2 = "203.0.113.156"
_IP_APT_3 = "203.0.113.157"


@dataclass
class ScenarioMeta:
    id: str
    name: str
    description: str
    severity: str
    mitre_tactics: list[str]
    mitre_techniques: list[str]
    threat_actor: str
    estimated_alerts: int
    duration_minutes: int


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _events_ssh_brute_force() -> list[EventCreate]:
    now = _now()
    events: list[EventCreate] = []
    base = now - timedelta(minutes=4)
    for i in range(14):
        events.append(EventCreate(
            timestamp=base + timedelta(seconds=i * 16),
            source_ip=_IP_BRUTE,
            destination_ip=_INTERNAL_DST,
            username="admin",
            event_type="authentication",
            status="failed",
            severity=Severity.medium,
            message="Failed password for admin",
            protocol="tcp",
            port=22,
            raw_log=f"sshd: Failed password for admin from {_IP_BRUTE} port {random.randint(40000, 65535)} ssh2",
            source_system="ssh",
        ))
    events.append(EventCreate(
        timestamp=now - timedelta(seconds=10),
        source_ip=_IP_BRUTE,
        destination_ip=_INTERNAL_DST,
        username="admin",
        event_type="authentication",
        status="success",
        severity=Severity.high,
        message="Accepted password for admin — attacker gained access",
        protocol="tcp",
        port=22,
        raw_log=f"sshd: Accepted password for admin from {_IP_BRUTE}",
        source_system="ssh",
    ))
    return sorted(events, key=lambda e: e.timestamp)


def _events_port_scan_exploit() -> list[EventCreate]:
    now = _now()
    events: list[EventCreate] = []
    scan_start = now - timedelta(minutes=3)
    for idx, port in enumerate(range(1, 21)):
        events.append(EventCreate(
            timestamp=scan_start + timedelta(seconds=idx * 5),
            source_ip=_IP_SCANNER,
            destination_ip=_INTERNAL_DST,
            event_type="network",
            status="attempt",
            severity=Severity.low,
            message="SYN scan probe",
            protocol="tcp",
            port=port,
            raw_log=f"SYN scan dst_port={port} src={_IP_SCANNER}",
            source_system="ids",
        ))
    exploit_targets = [80, 443, 8080, 8443, 3000]
    for i, port in enumerate(exploit_targets):
        events.append(EventCreate(
            timestamp=now - timedelta(minutes=1) + timedelta(seconds=i * 10),
            source_ip=_IP_SCANNER,
            destination_ip=_INTERNAL_DST,
            event_type="network",
            status="blocked",
            severity=Severity.high,
            message=f"Exploitation attempt on port {port} — CVE-pattern signature matched",
            protocol="tcp",
            port=port,
            raw_log=f"IDS ALERT exploit attempt {_IP_SCANNER}:{port}",
            source_system="ids",
        ))
    return sorted(events, key=lambda e: e.timestamp)


def _events_credential_stuffing() -> list[EventCreate]:
    now = _now()
    events: list[EventCreate] = []
    stuffing_ips = [_IP_STUFFING, _IP_APT_1, _IP_APT_2, _IP_APT_3,
                    "203.0.113.160", "203.0.113.161", "203.0.113.162", "203.0.113.163"]
    base = now - timedelta(minutes=4, seconds=30)
    for i in range(8):
        events.append(EventCreate(
            timestamp=base + timedelta(seconds=i * 18),
            source_ip=stuffing_ips[i % len(stuffing_ips)],
            destination_ip=_INTERNAL_DST,
            username="admin",
            event_type="authentication",
            status="failed",
            severity=Severity.medium,
            message="Credential stuffing: invalid password for admin",
            protocol="tcp",
            port=443,
            raw_log=f"oauth2 invalid_grant user=admin src={stuffing_ips[i % len(stuffing_ips)]}",
            source_system="idp",
        ))
    base2 = now - timedelta(minutes=2)
    for i in range(8):
        events.append(EventCreate(
            timestamp=base2 + timedelta(seconds=i * 18),
            source_ip=stuffing_ips[(i + 2) % len(stuffing_ips)],
            destination_ip=_INTERNAL_DST,
            username="jsmith",
            event_type="authentication",
            status="failed",
            severity=Severity.medium,
            message="Credential stuffing: invalid password for jsmith",
            protocol="tcp",
            port=443,
            raw_log=f"oauth2 invalid_grant user=jsmith src={stuffing_ips[(i + 2) % len(stuffing_ips)]}",
            source_system="idp",
        ))
    return sorted(events, key=lambda e: e.timestamp)


def _events_ransomware_chain() -> list[EventCreate]:
    now = _now()
    events: list[EventCreate] = []
    scan_start = now - timedelta(minutes=10)
    for idx, port in enumerate(range(3100, 3116)):
        events.append(EventCreate(
            timestamp=scan_start + timedelta(seconds=idx * 4),
            source_ip=_IP_RANSOM_C2,
            destination_ip=_INTERNAL_DST,
            event_type="network",
            status="attempt",
            severity=Severity.medium,
            message="Pre-ransomware reconnaissance scan",
            protocol="tcp",
            port=port,
            raw_log=f"scan dst_port={port} src={_IP_RANSOM_C2}",
            source_system="ids",
        ))
    lateral_ports = [445, 3389, 5985, 135, 139]
    lateral_start = now - timedelta(minutes=5)
    for i, port in enumerate(lateral_ports):
        events.append(EventCreate(
            timestamp=lateral_start + timedelta(seconds=i * 20),
            source_ip=_IP_RANSOM_C2,
            destination_ip=_INTERNAL_DST,
            event_type="network",
            status="success",
            severity=Severity.high,
            message=f"Lateral movement via port {port} — SMB/RDP/WinRM",
            protocol="tcp",
            port=port,
            raw_log=f"lateral_movement {_IP_RANSOM_C2}->{_INTERNAL_DST}:{port}",
            source_system="edr",
        ))
    malware_start = now - timedelta(minutes=1)
    for i in range(3):
        events.append(EventCreate(
            timestamp=malware_start + timedelta(seconds=i * 12),
            source_ip=_IP_RANSOM_C2,
            destination_ip=_INTERNAL_DST,
            event_type="malware",
            status="blocked",
            severity=Severity.critical,
            message="Ransomware signature detected — file encryption payload",
            protocol="tcp",
            port=443,
            raw_log=f"EDR BLOCK ransomware_payload src={_IP_RANSOM_C2}",
            source_system="edr",
        ))
    events.append(EventCreate(
        timestamp=now - timedelta(seconds=5),
        source_ip=_IP_RANSOM_C2,
        destination_ip=_INTERNAL_DST,
        event_type="endpoint",
        status="warning",
        severity=Severity.critical,
        message="File encryption activity detected — potential ransomware impact",
        protocol="tcp",
        port=445,
        raw_log="edr alert: mass_file_rename .encrypted extension",
        source_system="edr",
    ))
    return sorted(events, key=lambda e: e.timestamp)


def _events_data_exfiltration() -> list[EventCreate]:
    now = _now()
    events: list[EventCreate] = []
    dlp_start = now - timedelta(minutes=6)
    sensitive_files = [
        "HR_salary_Q4.xlsx",
        "customer_database_export.csv",
        "source_code_auth_module.zip",
        "executive_strategy_2026.pdf",
        "vpn_credentials_backup.txt",
    ]
    for i, fname in enumerate(sensitive_files):
        events.append(EventCreate(
            timestamp=dlp_start + timedelta(seconds=i * 30),
            source_ip=_IP_EXFIL,
            destination_ip=_INTERNAL_DST,
            username="contractor1",
            event_type="dlp",
            status="warning",
            severity=Severity.high,
            message=f"Sensitive file access: {fname}",
            protocol="tcp",
            port=445,
            raw_log=f"DLP WARN file_access user=contractor1 file={fname}",
            source_system="dlp",
        ))
    transfer_start = now - timedelta(minutes=2)
    for i in range(3):
        events.append(EventCreate(
            timestamp=transfer_start + timedelta(seconds=i * 25),
            source_ip=_IP_EXFIL,
            destination_ip="198.51.100.99",
            username="contractor1",
            event_type="network",
            status="allowed",
            severity=Severity.high,
            message="Large outbound data transfer to external host",
            protocol="tcp",
            port=443,
            raw_log=f"netflow src={_IP_EXFIL} dst=198.51.100.99 bytes={random.randint(50, 200)}MB",
            source_system="sensor",
        ))
    for i in range(2):
        events.append(EventCreate(
            timestamp=now - timedelta(seconds=20 - i * 8),
            source_ip=_IP_EXFIL,
            destination_ip="198.51.100.88",
            event_type="firewall",
            status="denied",
            severity=Severity.medium,
            message="Exfiltration attempt blocked by egress firewall",
            protocol="tcp",
            port=21,
            raw_log=f"DROP {_IP_EXFIL}->198.51.100.88:21 policy=no_ftp_egress",
            source_system="fw",
        ))
    return sorted(events, key=lambda e: e.timestamp)


def _events_apt_lateral_movement() -> list[EventCreate]:
    now = _now()
    events: list[EventCreate] = []
    events.append(EventCreate(
        timestamp=now - timedelta(minutes=15),
        source_ip=_IP_APT_1,
        destination_ip=_INTERNAL_DST,
        username="svc_backup",
        event_type="authentication",
        status="success",
        severity=Severity.high,
        message="Privileged account login from new geographic location",
        protocol="tcp",
        port=443,
        raw_log=f"idp: new_location_login user=svc_backup src={_IP_APT_1}",
        source_system="idp",
    ))
    persist_start = now - timedelta(minutes=12)
    persist_tasks = [
        "Scheduled task created: WindowsUpdateHelper",
        "Registry run key added: HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
        "New service installed: SvcHostHelper",
    ]
    for i, msg in enumerate(persist_tasks):
        events.append(EventCreate(
            timestamp=persist_start + timedelta(seconds=i * 40),
            source_ip=_IP_APT_1,
            destination_ip=_INTERNAL_DST,
            username="svc_backup",
            event_type="admin_access",
            status="success",
            severity=Severity.high,
            message=msg,
            protocol="tcp",
            port=135,
            raw_log=f"sysmon: {msg.lower().replace(' ', '_')}",
            source_system="edr",
        ))
    discovery_start = now - timedelta(minutes=7)
    for i in range(5):
        events.append(EventCreate(
            timestamp=discovery_start + timedelta(seconds=i * 18),
            source_ip=_IP_APT_1,
            destination_ip=f"10.0.{random.randint(1, 5)}.{random.randint(1, 50)}",
            event_type="network",
            status="info",
            severity=Severity.medium,
            message="Internal host enumeration — ARP/NetBIOS sweep",
            protocol="tcp",
            port=137,
            raw_log=f"netbios sweep src={_IP_APT_1}",
            source_system="ids",
        ))
    denied_start = now - timedelta(minutes=4)
    for i in range(22):
        events.append(EventCreate(
            timestamp=denied_start + timedelta(seconds=i * 9),
            source_ip=_IP_APT_2,
            destination_ip=_INTERNAL_DST,
            event_type="firewall",
            status="denied",
            severity=Severity.low,
            message="Blocked connection — policy violation",
            protocol="tcp",
            port=random.choice([22, 445, 3389, 1433, 5432, 8080]),
            raw_log=f"DROP {_IP_APT_2}->{_INTERNAL_DST}",
            source_system="fw",
        ))
    lateral_start = now - timedelta(minutes=1)
    lateral_targets = ["10.0.1.20", "10.0.2.15", "10.0.3.8", "10.0.4.30"]
    for i, dst in enumerate(lateral_targets):
        events.append(EventCreate(
            timestamp=lateral_start + timedelta(seconds=i * 12),
            source_ip=_IP_APT_3,
            destination_ip=dst,
            username="svc_backup",
            event_type="network",
            status="success",
            severity=Severity.high,
            message="Lateral movement via SMB — pass-the-hash detected",
            protocol="tcp",
            port=445,
            raw_log=f"lateral_smb {_IP_APT_3}->{dst} user=svc_backup pass_the_hash=true",
            source_system="edr",
        ))
    return sorted(events, key=lambda e: e.timestamp)


SCENARIOS: dict[str, ScenarioMeta] = {
    "ssh_brute_force": ScenarioMeta(
        id="ssh_brute_force",
        name="SSH Brute Force Campaign",
        description="Attacker hammers SSH with password guessing until gaining access. Triggers the brute force detection rule and generates a high-severity incident.",
        severity="high",
        mitre_tactics=["Credential Access"],
        mitre_techniques=["T1110.003"],
        threat_actor="Generic opportunistic attacker",
        estimated_alerts=1,
        duration_minutes=5,
    ),
    "port_scan_exploit": ScenarioMeta(
        id="port_scan_exploit",
        name="Reconnaissance & Service Exploitation",
        description="Attacker performs a full port scan to map the network, then launches exploitation attempts against discovered web services.",
        severity="high",
        mitre_tactics=["Discovery", "Initial Access"],
        mitre_techniques=["T1046", "T1190"],
        threat_actor="Opportunistic threat actor",
        estimated_alerts=1,
        duration_minutes=3,
    ),
    "credential_stuffing": ScenarioMeta(
        id="credential_stuffing",
        name="Credential Stuffing Attack",
        description="Attacker rotates through proxy IPs to spray stolen credential pairs against the authentication service, targeting multiple accounts.",
        severity="medium",
        mitre_tactics=["Credential Access"],
        mitre_techniques=["T1110.004"],
        threat_actor="Cybercrime group with credential database",
        estimated_alerts=2,
        duration_minutes=5,
    ),
    "ransomware_chain": ScenarioMeta(
        id="ransomware_chain",
        name="Ransomware Kill Chain",
        description="Full ransomware campaign: reconnaissance scan → lateral movement via SMB/RDP → payload delivery and file encryption. Multiple alerts across kill chain stages.",
        severity="critical",
        mitre_tactics=["Discovery", "Lateral Movement", "Impact"],
        mitre_techniques=["T1046", "T1021.001", "T1486"],
        threat_actor="Ransomware-as-a-Service operator",
        estimated_alerts=2,
        duration_minutes=10,
    ),
    "data_exfiltration": ScenarioMeta(
        id="data_exfiltration",
        name="Insider Data Exfiltration",
        description="Malicious insider accesses sensitive files via DLP-monitored shares then attempts to exfiltrate data to external hosts over HTTPS and FTP.",
        severity="high",
        mitre_tactics=["Collection", "Exfiltration"],
        mitre_techniques=["T1560", "T1048"],
        threat_actor="Malicious insider / compromised contractor",
        estimated_alerts=1,
        duration_minutes=6,
    ),
    "apt_lateral_movement": ScenarioMeta(
        id="apt_lateral_movement",
        name="APT Lateral Movement Campaign",
        description="Nation-state style attack: initial access via stolen service account → persistence via scheduled tasks → internal host discovery → lateral movement with pass-the-hash.",
        severity="critical",
        mitre_tactics=["Initial Access", "Persistence", "Discovery", "Lateral Movement"],
        mitre_techniques=["T1078", "T1053", "T1018", "T1021"],
        threat_actor="Advanced Persistent Threat (APT)",
        estimated_alerts=2,
        duration_minutes=15,
    ),
}

_SCENARIO_GENERATORS = {
    "ssh_brute_force": _events_ssh_brute_force,
    "port_scan_exploit": _events_port_scan_exploit,
    "credential_stuffing": _events_credential_stuffing,
    "ransomware_chain": _events_ransomware_chain,
    "data_exfiltration": _events_data_exfiltration,
    "apt_lateral_movement": _events_apt_lateral_movement,
}


def get_scenario_events(scenario_id: str) -> list[EventCreate]:
    generator = _SCENARIO_GENERATORS.get(scenario_id)
    if generator is None:
        raise KeyError(scenario_id)
    return generator()
