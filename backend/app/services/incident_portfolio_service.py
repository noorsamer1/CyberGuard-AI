"""Aggregate incident data for portfolio AI reports (deterministic stats + chart payloads)."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.enums import IncidentStatus, Severity
from app.models.event import Event
from app.models.incident import Incident, incident_events
from app.services.mitre_service import get_alert_threat_intel

DEFAULT_PORTFOLIO_MAX_ITEMS = 150


def detect_spike_last_period(weekly_created: list[dict[str, Any]]) -> bool:
    """True if the most recent bucket is a clear spike vs prior average (for AI callouts)."""
    if len(weekly_created) < 4:
        return False
    counts = [int(b["count"]) for b in weekly_created]
    last = counts[-1]
    prev = counts[:-1]
    baseline = sum(prev) / len(prev) if prev else 0.0
    if baseline <= 0:
        return False
    return last >= 2 * baseline and last >= max(prev) + 1


def _incident_filter_conditions(
    owner_id: int,
    status: Optional[IncidentStatus],
    severity: Optional[Severity],
    q: Optional[str],
) -> list[Any]:
    conds: list[Any] = [Incident.owner_id == owner_id]
    if status is not None:
        conds.append(Incident.status == status)
    if severity is not None:
        conds.append(Incident.severity == severity)
    if q:
        like = f"%{q}%"
        conds.append(or_(Incident.title.ilike(like), Incident.summary.ilike(like)))
    return conds


def _severity_value(sev: Severity) -> str:
    return sev.value if hasattr(sev, "value") else str(sev)


def _status_value(st: IncidentStatus) -> str:
    return st.value if hasattr(st, "value") else str(st)


def build_portfolio_payload(
    db: Session,
    *,
    owner_id: int,
    status: Optional[IncidentStatus] = None,
    severity: Optional[Severity] = None,
    q: Optional[str] = None,
    max_items: int = DEFAULT_PORTFOLIO_MAX_ITEMS,
) -> dict[str, Any]:
    """Build stats and chart-ready structures for the incident portfolio report."""
    conds = _incident_filter_conditions(owner_id, status, severity, q)
    where_clause = and_(*conds) if conds else True

    total_matching = int(db.scalar(select(func.count()).select_from(Incident).where(where_clause)) or 0)

    cap = max(1, min(int(max_items), 500))

    # Severity distribution (full filtered set)
    sev_rows = db.execute(
        select(Incident.severity, func.count(Incident.id))
        .where(where_clause)
        .group_by(Incident.severity)
    ).all()
    severity_counts: dict[str, int] = {s.value: 0 for s in Severity}
    for sev, cnt in sev_rows:
        severity_counts[_severity_value(sev)] = int(cnt)

    # Status distribution
    st_rows = db.execute(
        select(Incident.status, func.count(Incident.id))
        .where(where_clause)
        .group_by(Incident.status)
    ).all()
    status_counts: dict[str, int] = {}
    for st, cnt in st_rows:
        status_counts[_status_value(st)] = int(cnt)

    # Weekly timeline (PostgreSQL date_trunc)
    week_col = func.date_trunc("week", Incident.created_at).label("week_start")
    tl_rows = db.execute(
        select(week_col, func.count(Incident.id))
        .where(where_clause)
        .group_by(week_col)
        .order_by(week_col)
    ).all()
    weekly_created: list[dict[str, Any]] = []
    for week_start, cnt in tl_rows:
        ws = week_start
        if ws is not None and hasattr(ws, "isoformat"):
            weekly_created.append({"week_start": ws.isoformat(), "count": int(cnt)})
        elif ws is not None:
            weekly_created.append({"week_start": str(ws), "count": int(cnt)})

    spike_last_period = detect_spike_last_period(weekly_created)

    # Oldest open / investigating backlog (top 10)
    open_statuses = (IncidentStatus.open, IncidentStatus.investigating)
    oldest_stmt = (
        select(Incident.id, Incident.title, Incident.created_at)
        .where(where_clause, Incident.status.in_(open_statuses))
        .order_by(Incident.created_at.asc())
        .limit(10)
    )
    now = datetime.now(timezone.utc)
    oldest_open: list[dict[str, Any]] = []
    for iid, title, created_at in db.execute(oldest_stmt).all():
        ca = created_at
        if ca.tzinfo is None:
            ca = ca.replace(tzinfo=timezone.utc)
        days_open = max(0, int((now - ca).total_seconds() // 86400))
        oldest_open.append(
            {
                "id": int(iid),
                "title": (title or "")[:200],
                "created_at": ca.isoformat(),
                "days_open": days_open,
            }
        )

    # Capped sample for titles + rule rollup (newest first)
    sample_stmt = (
        select(Incident.id, Incident.title, Incident.summary, Incident.created_at)
        .where(where_clause)
        .order_by(Incident.created_at.desc())
        .limit(cap)
    )
    sample_rows = list(db.execute(sample_stmt).all())
    sample_ids = [int(r[0]) for r in sample_rows]
    truncated = total_matching > len(sample_rows)
    truncation_note: str | None = None
    if truncated:
        truncation_note = (
            f"Showing newest {len(sample_rows)} of {total_matching} matching incidents "
            f"(cap={cap}). Distributions and timeline use the full filtered set."
        )

    sample_titles: list[dict[str, str]] = []
    for iid, title, summary, _ca in sample_rows:
        sample_titles.append(
            {
                "id": str(iid),
                "title": (title or "")[:300],
                "summary": (summary or "")[:400],
            }
        )

    # Rule names from alerts linked to events on sampled incidents
    rule_counter: Counter[str] = Counter()
    if sample_ids:
        rule_q = (
            select(Alert.rule_name, func.count())
            .select_from(incident_events)
            .join(Event, Event.id == incident_events.c.event_id)
            .join(Alert, Alert.event_id == Event.id)
            .where(incident_events.c.incident_id.in_(sample_ids))
            .where(Alert.rule_name.isnot(None))
            .group_by(Alert.rule_name)
        )
        for rn, cnt in db.execute(rule_q).all():
            if rn:
                rule_counter[str(rn)] += int(cnt)

    rule_counts_chart = [{"rule_name": k, "count": v} for k, v in rule_counter.most_common(15)]

    mitre_counter: Counter[str] = Counter()
    mitre_labels: dict[str, str] = {}
    for rule, weight in rule_counter.items():
        techniques, _ = get_alert_threat_intel(rule)
        for t in techniques:
            mitre_counter[t.technique_id] += weight
            mitre_labels[t.technique_id] = f"{t.tactic}: {t.technique} ({t.technique_id})"

    mitre_top = [
        {"technique_id": tid, "label": mitre_labels.get(tid, tid), "count": c}
        for tid, c in mitre_counter.most_common(12)
    ]

    stats: dict[str, Any] = {
        "total_matching": total_matching,
        "sample_size": len(sample_rows),
        "severity_counts": severity_counts,
        "status_counts": status_counts,
        "weekly_created": weekly_created,
        "spike_last_period": spike_last_period,
        "oldest_open": oldest_open,
        "rule_counts": rule_counts_chart,
        "mitre_top": mitre_top,
        "sample_titles": sample_titles[:50],
    }

    charts = {
        "severity_bar": [{"name": k, "count": v} for k, v in severity_counts.items() if v > 0],
        "status_bar": [{"name": k.replace("_", " "), "count": v} for k, v in status_counts.items()],
        "weekly_line": weekly_created,
        "rules_bar": rule_counts_chart,
        "mitre_bar": mitre_top,
    }

    return {
        "generated_at": now.isoformat(),
        "filters": {
            "status": status.value if status else None,
            "severity": severity.value if severity else None,
            "q": q or None,
        },
        "max_items": cap,
        "truncated": truncated,
        "truncation_note": truncation_note,
        "stats": stats,
        "charts": charts,
    }
