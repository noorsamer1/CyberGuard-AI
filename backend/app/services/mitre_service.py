from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MitreTechnique:
    tactic: str
    technique: str
    technique_id: str
    sub_technique: str | None = None


@dataclass(frozen=True)
class ThreatProfile:
    actor: str
    confidence: str
    cve_references: list[str]
    kill_chain_phase: str


_RULE_TO_MITRE: dict[str, list[MitreTechnique]] = {
    "brute_force": [
        MitreTechnique(
            tactic="Credential Access",
            technique="Brute Force",
            technique_id="T1110",
            sub_technique="T1110.003 Password Spraying",
        )
    ],
    "failed_login_burst": [
        MitreTechnique(
            tactic="Credential Access",
            technique="Brute Force",
            technique_id="T1110",
            sub_technique="T1110.004 Credential Stuffing",
        )
    ],
    "port_scan": [
        MitreTechnique(
            tactic="Discovery",
            technique="Network Service Scanning",
            technique_id="T1046",
        )
    ],
    "denied_access_spike": [
        MitreTechnique(
            tactic="Defense Evasion",
            technique="Impair Defenses",
            technique_id="T1562",
        )
    ],
    "event_rate_anomaly": [
        MitreTechnique(
            tactic="Impact",
            technique="Service Exhaustion",
            technique_id="T1499",
        )
    ],
    "data_exfiltration": [
        MitreTechnique(
            tactic="Collection",
            technique="Archive Collected Data",
            technique_id="T1560",
        ),
        MitreTechnique(
            tactic="Exfiltration",
            technique="Exfiltration Over Alternative Protocol",
            technique_id="T1048",
        ),
    ],
    "sql_injection_attempt": [
        MitreTechnique(
            tactic="Initial Access",
            technique="Exploit Public-Facing Application",
            technique_id="T1190",
        )
    ],
    "path_traversal_attempt": [
        MitreTechnique(
            tactic="Discovery",
            technique="File and Directory Discovery",
            technique_id="T1083",
        )
    ],
    "suspicious_upload_misuse": [
        MitreTechnique(
            tactic="Initial Access",
            technique="Exploit Public-Facing Application",
            technique_id="T1190",
        )
    ],
    "ransomware_simulation": [
        MitreTechnique(
            tactic="Impact",
            technique="Data Encrypted for Impact",
            technique_id="T1486",
        )
    ],
}

_RULE_TO_PROFILE: dict[str, ThreatProfile] = {
    "brute_force": ThreatProfile(
        actor="APT28 / Commodity Botnet Pattern",
        confidence="medium",
        cve_references=["CWE-307"],
        kill_chain_phase="Credential Access",
    ),
    "failed_login_burst": ThreatProfile(
        actor="Credential Stuffing Operations",
        confidence="medium",
        cve_references=["CWE-307", "CWE-287"],
        kill_chain_phase="Credential Access",
    ),
    "port_scan": ThreatProfile(
        actor="Lazarus-style Recon Pattern",
        confidence="high",
        cve_references=["CVE-2023-44487", "CVE-2024-3094"],
        kill_chain_phase="Reconnaissance",
    ),
    "denied_access_spike": ThreatProfile(
        actor="Opportunistic Scanner / WAF Probe",
        confidence="low",
        cve_references=["CWE-693"],
        kill_chain_phase="Defense Evasion",
    ),
    "event_rate_anomaly": ThreatProfile(
        actor="DDoS / Service Exhaustion Pattern",
        confidence="medium",
        cve_references=["CVE-2024-2169"],
        kill_chain_phase="Impact",
    ),
    "data_exfiltration": ThreatProfile(
        actor="Malicious Insider / Compromised Contractor",
        confidence="high",
        cve_references=["CWE-200", "CWE-201"],
        kill_chain_phase="Collection and Exfiltration",
    ),
    "sql_injection_attempt": ThreatProfile(
        actor="Web Application Attack Pattern",
        confidence="high",
        cve_references=["CWE-89"],
        kill_chain_phase="Initial Access",
    ),
    "path_traversal_attempt": ThreatProfile(
        actor="Web Application Attack Pattern",
        confidence="high",
        cve_references=["CWE-22"],
        kill_chain_phase="Discovery",
    ),
    "suspicious_upload_misuse": ThreatProfile(
        actor="Web Application Attack Pattern",
        confidence="medium",
        cve_references=["CWE-434"],
        kill_chain_phase="Initial Access",
    ),
    "ransomware_simulation": ThreatProfile(
        actor="Ransomware Behavior Pattern",
        confidence="high",
        cve_references=["CWE-693"],
        kill_chain_phase="Impact",
    ),
}


def get_alert_threat_intel(rule_name: str) -> tuple[list[MitreTechnique], ThreatProfile | None]:
    techniques = _RULE_TO_MITRE.get(rule_name, [])
    profile = _RULE_TO_PROFILE.get(rule_name)
    return techniques, profile


def get_incident_threat_intel(rule_names: list[str]) -> tuple[list[MitreTechnique], list[ThreatProfile]]:
    techniques: list[MitreTechnique] = []
    profiles: list[ThreatProfile] = []
    seen_techniques: set[str] = set()
    seen_actors: set[str] = set()

    for rule_name in rule_names:
        rule_techniques, profile = get_alert_threat_intel(rule_name)
        for t in rule_techniques:
            if t.technique_id in seen_techniques:
                continue
            seen_techniques.add(t.technique_id)
            techniques.append(t)
        if profile and profile.actor not in seen_actors:
            seen_actors.add(profile.actor)
            profiles.append(profile)

    return techniques, profiles
