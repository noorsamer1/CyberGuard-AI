import json
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def analyze_incident_context(
    incident_title: str,
    incident_summary: str,
    event_snippets: list[dict[str, Any]],
) -> Optional[dict[str, str]]:
    if not settings.openrouter_api_key:
        logger.info("OpenRouter API key not set; skipping AI analysis")
        return None
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a senior SOC analyst. Respond with compact JSON only, no markdown. "
                    "Keys: summary, why_suspicious, remediation, executive_summary, analyst_notes."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "incident_title": incident_title,
                        "incident_summary": incident_summary,
                        "related_events": event_snippets[:50],
                    }
                ),
            },
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": "https://cyberguard.local",
        "X-Title": "CyberGuard AI",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(OPENROUTER_URL, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"]
            text = text.strip()
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json"):
                    text = text[4:].strip()
            parsed = json.loads(text)
            return {
                "summary": str(parsed.get("summary", "")),
                "why_suspicious": str(parsed.get("why_suspicious", "")),
                "remediation": str(parsed.get("remediation", "")),
                "executive_summary": str(parsed.get("executive_summary", "")),
                "analyst_notes": str(parsed.get("analyst_notes", "")),
            }
    except Exception as e:
        logger.warning("AI analysis failed: %s", e)
        return None


ALLOWED_ATTACK_TYPES = {
    "brute_force",
    "sql_injection",
    "path_traversal",
    "port_scan",
    "data_exfiltration",
    "ransomware",
    "suspicious_upload",
    "denied_access_spike",
    "rate_anomaly",
    "lateral_movement",
    "benign",
    "unknown",
}

ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}


def classify_event_context(event_context: dict[str, Any]) -> Optional[dict[str, Any]]:
    if not settings.openrouter_api_key:
        logger.info("OpenRouter API key not set; skipping AI event classification")
        return None
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a senior SOC detection copilot. Respond with compact JSON only, no markdown. "
                    "Classify exactly one security event using only the provided fields. "
                    "Allowed attack_type values: brute_force, sql_injection, path_traversal, port_scan, "
                    "data_exfiltration, ransomware, suspicious_upload, denied_access_spike, rate_anomaly, "
                    "lateral_movement, benign, unknown. "
                    "Keys: attack_type, confidence, suggested_severity, why_classified, evidence, "
                    "mitre_tactics, mitre_techniques, recommended_actions, should_create_alert. "
                    "evidence must quote or closely cite exact observed indicators from the event fields. "
                    "Use should_create_alert=false for benign, unknown, weak, or ambiguous evidence."
                ),
            },
            {"role": "user", "content": json.dumps({"event": event_context}, default=str)},
        ],
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": "https://cyberguard.local",
        "X-Title": "CyberGuard AI",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.post(OPENROUTER_URL, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"].strip()
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json"):
                    text = text[4:].strip()
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                return None
            attack_type = str(parsed.get("attack_type") or "unknown").strip().lower()
            if attack_type not in ALLOWED_ATTACK_TYPES:
                attack_type = "unknown"
            severity = str(parsed.get("suggested_severity") or "low").strip().lower()
            if severity not in ALLOWED_SEVERITIES:
                severity = "low"
            confidence = parsed.get("confidence", 0.0)
            try:
                confidence_float = max(0.0, min(float(confidence), 1.0))
            except (TypeError, ValueError):
                confidence_float = 0.0
            return {
                "attack_type": attack_type,
                "confidence": confidence_float,
                "suggested_severity": severity,
                "why_classified": str(parsed.get("why_classified") or "")[:4000],
                "evidence": _string_list(parsed.get("evidence"), max_items=8),
                "mitre_tactics": _string_list(parsed.get("mitre_tactics"), max_items=8),
                "mitre_techniques": _string_list(parsed.get("mitre_techniques"), max_items=8),
                "recommended_actions": _string_list(parsed.get("recommended_actions"), max_items=8),
                "should_create_alert": bool(parsed.get("should_create_alert")),
                "raw_response": parsed,
            }
    except Exception as e:
        logger.warning("AI event classification failed: %s", e)
        return None


def _string_list(value: Any, max_items: int) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value[:max_items]:
        text = str(item).strip()
        if text:
            out.append(text[:500])
    return out
