"""Aggregate alert data for SOC portfolio PDF reports."""



from __future__ import annotations



from collections import Counter

from datetime import datetime, timezone

from typing import Any, Optional



from app.models.alert import Alert

from app.models.enums import AlertStatus, Severity

from app.services.mitre_service import get_alert_threat_intel





def _build_executive_summary(

    *,

    total: int,

    correlated_events: int,

    critical_high: int,

    open_count: int,

    sev_counts: dict[str, int],

    top_rule: str | None,

    top_attack: str | None,

    top_ip: str | None,

    date_range: str,

) -> str:

    """Generate a short analyst-style executive summary from aggregate stats."""

    if total == 0:

        return (

            "No alerts match the current export filters. Adjust severity or status filters "

            "on the Alerts page and regenerate the portfolio report."

        )

    lines = [

        f"This portfolio covers {total} alert(s) spanning {date_range}, "

        f"representing {correlated_events} correlated telemetry event(s).",

    ]

    if critical_high:

        lines.append(

            f"{critical_high} alert(s) are rated critical or high — these should be triaged "

            "before lower-severity noise."

        )

    else:

        lines.append("No critical or high-severity alerts appear in this export.")

    if open_count:

        lines.append(

            f"{open_count} alert(s) remain open or new and may still require analyst action."

        )

    dominant_sev = max(sev_counts, key=sev_counts.get) if sev_counts else None

    if dominant_sev:

        lines.append(

            f"The dominant severity band is {dominant_sev} ({sev_counts[dominant_sev]} alert(s))."

        )

    intel_bits = []

    if top_rule:

        intel_bits.append(f"top rule: {top_rule}")

    if top_attack:

        intel_bits.append(f"top attack type: {top_attack}")

    if top_ip:

        intel_bits.append(f"top source IP: {top_ip}")

    if intel_bits:

        lines.append("Threat highlights — " + "; ".join(intel_bits) + ".")

    return " ".join(lines)





def build_alert_portfolio_context(

    alerts: list[Alert],

    *,

    severity_filter: Optional[Severity] = None,

    status_filter: Optional[AlertStatus] = None,

) -> dict[str, Any]:

    """Build deterministic stats and chart payloads for alert portfolio PDF."""

    sev_counts: Counter[str] = Counter()

    status_counts: Counter[str] = Counter()

    rule_counts: Counter[str] = Counter()

    attack_counts: Counter[str] = Counter()

    mitre_counts: Counter[str] = Counter()

    source_ip_counts: Counter[str] = Counter()

    day_buckets: Counter[str] = Counter()

    hour_buckets: Counter[str] = Counter()

    correlated_events = 0

    open_statuses = {AlertStatus.new.value, AlertStatus.acknowledged.value}



    rows: list[dict[str, str]] = []

    timestamps: list[datetime] = []



    for alert in alerts:

        sev_counts[alert.severity.value if alert.severity else "unknown"] += 1

        status_counts[alert.status.value if alert.status else "unknown"] += 1

        rule_counts[alert.rule_name or "unknown"] += 1

        attack_key = (alert.attack_type or "unknown").replace("_", " ")

        attack_counts[attack_key] += 1

        correlated_events += alert.event_count or 1



        techniques, _ = get_alert_threat_intel(alert.rule_name)

        for tech in techniques[:2]:

            mitre_counts[tech.technique_id] += 1



        if alert.created_at:

            timestamps.append(alert.created_at)

            day_buckets[alert.created_at.strftime("%Y-%m-%d")] += 1

            hour_buckets[alert.created_at.strftime("%Y-%m-%d %H:00")] += 1



        source_ip = "—"

        if alert.event and alert.event.source_ip:

            source_ip = alert.event.source_ip

            source_ip_counts[source_ip] += 1



        rows.append(

            {

                "id": str(alert.id),

                "title": (alert.title or "")[:48],

                "rule": (alert.rule_name or "")[:22],

                "severity": alert.severity.value if alert.severity else "—",

                "status": alert.status.value if alert.status else "—",

                "source_ip": source_ip[:18],

                "events": str(alert.event_count or 1),

                "triggered": alert.created_at.strftime("%Y-%m-%d %H:%M") if alert.created_at else "",

            }

        )



    filter_parts = []

    if severity_filter:

        filter_parts.append(f"severity={severity_filter.value}")

    if status_filter:

        filter_parts.append(f"status={status_filter.value}")

    filter_label = ", ".join(filter_parts) if filter_parts else "all alerts"



    critical_high = sev_counts.get("critical", 0) + sev_counts.get("high", 0)

    open_count = sum(status_counts.get(s, 0) for s in open_statuses)

    resolved_count = status_counts.get(AlertStatus.resolved.value, 0)



    if timestamps:

        start = min(timestamps).strftime("%Y-%m-%d %H:%M UTC")

        end = max(timestamps).strftime("%Y-%m-%d %H:%M UTC")

        date_range = f"{start} → {end}" if start != end else start

    else:

        date_range = "no timestamps"



    if len(day_buckets) >= 2:

        timeline_buckets = dict(sorted(day_buckets.items()))

    elif len(hour_buckets) >= 1:

        timeline_buckets = dict(sorted(hour_buckets.items()))

    else:

        timeline_buckets = dict(sorted(day_buckets.items()))



    top_rule = rule_counts.most_common(1)[0][0] if rule_counts else None

    top_attack = attack_counts.most_common(1)[0][0] if attack_counts else None

    top_ip = source_ip_counts.most_common(1)[0][0] if source_ip_counts else None



    return {

        "generated_at": datetime.now(timezone.utc).isoformat(),

        "filter_label": filter_label,

        "total_alerts": len(alerts),

        "correlated_events": correlated_events,

        "critical_high_count": critical_high,

        "open_count": open_count,

        "resolved_count": resolved_count,

        "unique_source_ips": len(source_ip_counts),

        "date_range": date_range,

        "executive_summary": _build_executive_summary(

            total=len(alerts),

            correlated_events=correlated_events,

            critical_high=critical_high,

            open_count=open_count,

            sev_counts=dict(sev_counts),

            top_rule=top_rule,

            top_attack=top_attack,

            top_ip=top_ip,

            date_range=date_range,

        ),

        "severity_counts": dict(sev_counts),

        "status_counts": dict(status_counts),

        "rule_counts": dict(rule_counts.most_common(12)),

        "attack_counts": dict(attack_counts.most_common(10)),

        "mitre_counts": dict(mitre_counts.most_common(10)),

        "source_ip_counts": dict(source_ip_counts.most_common(10)),

        "day_buckets": dict(sorted(day_buckets.items())),

        "hour_buckets": dict(sorted(hour_buckets.items())),

        "timeline_buckets": timeline_buckets,

        "alert_rows": rows[:80],

    }

