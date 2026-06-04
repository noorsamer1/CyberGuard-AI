from __future__ import annotations

import io
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

import plotly.graph_objects as go

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings
from app.models.enums import Severity
from app.models.incident import Incident
from app.services.incident_report_context import (
    IncidentReportContext,
    build_incident_report_context,
    context_to_dict,
    format_duration,
)

logger = logging.getLogger(__name__)


def ensure_reports_dir() -> Path:
    p = Path(settings.reports_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _severity_band_color(sev: Severity) -> colors.Color:
    return {
        Severity.low: colors.HexColor("#3b82f6"),
        Severity.medium: colors.HexColor("#eab308"),
        Severity.high: colors.HexColor("#f97316"),
        Severity.critical: colors.HexColor("#dc2626"),
    }.get(sev, colors.HexColor("#64748b"))


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    safe = escape(text or "").replace("\n", "<br/>")
    return Paragraph(safe, style)


def _plotly_fig_to_png(fig: go.Figure, width: int = 880, height: int = 380) -> io.BytesIO | None:
    try:
        raw = fig.to_image(format="png", width=width, height=height, scale=1, engine="kaleido")
        buf = io.BytesIO(raw)
        buf.seek(0)
        return buf
    except Exception:
        logger.warning("Plotly/Kaleido PNG export failed; chart omitted from PDF.", exc_info=True)
        return None


def _incident_event_charts(
    evs: list,
    incident_title: str,
) -> list[tuple[io.BytesIO, str]]:
    """Returns list of (png_buffer, caption) for meaningful incident visuals."""
    out: list[tuple[io.BytesIO, str]] = []
    if not evs:
        return out

    # 1) Volume by event type — what kinds of telemetry dominate this incident
    counts = Counter((e.event_type or "unknown") for e in evs)
    top = counts.most_common(12)
    labels = [k[:22] for k, _ in top]
    vals = [v for _, v in top]
    fig1 = go.Figure(
        data=[
            go.Bar(
                x=vals,
                y=labels,
                orientation="h",
                marker=dict(color="#22d3ee", line=dict(color="#164e63", width=1)),
            )
        ]
    )
    fig1.update_layout(
        title=dict(text="Related events by type", font=dict(color="#f1f5f9", size=16)),
        paper_bgcolor="#0f172a",
        plot_bgcolor="#1e293b",
        font=dict(color="#e2e8f0", size=11),
        margin=dict(l=12, r=12, t=48, b=48),
        xaxis=dict(title="Count", gridcolor="#334155", color="#94a3b8"),
        yaxis=dict(gridcolor="#334155", color="#94a3b8", autorange="reversed"),
        height=380,
        width=880,
    )
    buf1 = _plotly_fig_to_png(fig1)
    if buf1:
        cap1 = (
            "This chart shows how many linked events fall into each event type (e.g. authentication, network). "
            "Higher bars highlight the dominant signal classes the analyst should review first when validating the incident narrative."
        )
        out.append((buf1, cap1))

    # 2) Timeline — when activity clustered (UTC hour buckets)
    buckets: Counter[str] = Counter()
    for e in evs:
        if e.timestamp:
            buckets[e.timestamp.strftime("%Y-%m-%d %H:00")] += 1
    if len(buckets) >= 2 or (len(buckets) == 1 and next(iter(buckets.values())) > 1):
        times = sorted(buckets.keys())
        counts_t = [buckets[t] for t in times]
        fig2 = go.Figure(
            data=[
                go.Scatter(
                    x=times,
                    y=counts_t,
                    mode="lines+markers",
                    line=dict(color="#a78bfa", width=2),
                    marker=dict(size=8, color="#c4b5fd"),
                    fill="tozeroy",
                    fillcolor="rgba(167,139,250,0.12)",
                )
            ]
        )
        fig2.update_layout(
            title=dict(text="Event volume over time (UTC, hourly buckets)", font=dict(color="#f1f5f9", size=16)),
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            font=dict(color="#e2e8f0", size=10),
            margin=dict(l=12, r=12, t=48, b=80),
            xaxis=dict(title="Hour (UTC)", gridcolor="#334155", color="#94a3b8", tickangle=-35),
            yaxis=dict(title="Events", gridcolor="#334155", color="#94a3b8"),
            height=380,
            width=880,
        )
        buf2 = _plotly_fig_to_png(fig2)
        if buf2:
            cap2 = (
                "Buckets aggregate linked events by hour (UTC). Spikes often align with attack phases "
                f'(e.g. scan then brute force). Cross-check with the incident title: "{(incident_title or "")[:80]}".'
            )
            out.append((buf2, cap2))

    return out


def _incident_ai_classification_rows(evs: list) -> list[list[str]]:
    rows: list[list[str]] = []
    for ev in evs:
        item = getattr(ev, "ai_classification", None)
        if not item:
            continue
        rows.append(
            [
                f"#{ev.id}",
                (item.attack_type or "unknown").replace("_", " "),
                f"{float(item.confidence or 0.0):.0%}",
                str(item.suggested_severity or "low"),
                (item.why_classified or "")[:90],
            ]
        )
    return rows


def _digest_severity_chart_png(
    min_severity: Severity,
    sev_counts: Counter,
) -> tuple[io.BytesIO | None, str]:
    names = [s.value for s in _severity_order()]
    vals = [sev_counts.get(s, 0) for s in _severity_order()]
    colors_bar = ["#3b82f6", "#eab308", "#f97316", "#dc2626"]
    label = "all severities" if min_severity == Severity.low else f"{min_severity.value} and above"
    fig = go.Figure(
        data=[
            go.Bar(
                x=names,
                y=vals,
                marker=dict(color=colors_bar, line=dict(color="#1e293b", width=1)),
            )
        ]
    )
    fig.update_layout(
        title=dict(text=f"Incidents in window ({label})", font=dict(color="#f1f5f9", size=16)),
        paper_bgcolor="#0f172a",
        plot_bgcolor="#1e293b",
        font=dict(color="#e2e8f0", size=11),
        margin=dict(l=12, r=12, t=48, b=48),
        xaxis=dict(title="Severity", gridcolor="#334155"),
        yaxis=dict(title="Count", gridcolor="#334155"),
        height=320,
        width=800,
    )
    buf = _plotly_fig_to_png(fig, width=800, height=320)
    caption = (
        "Counts include only incidents at or above the schedule’s minimum severity. "
        "Use this to see whether the period was dominated by lower noise versus high/critical work."
    )
    return buf, caption


def _render_deterministic_context(story: list, ctx: IncidentReportContext, h2, body, meta) -> None:
    """Append deterministic status/context sections to the PDF story."""
    story.append(Paragraph("Incident status and metrics", h2))
    story.append(
        _p(
            f"Status: {ctx.incident_status} · Events linked: {ctx.event_count} · "
            f"MTTA: {format_duration(ctx.mtta_seconds)} · "
            f"MTTR: {format_duration(ctx.mttr_seconds)}",
            body,
        )
    )
    story.append(_p(f"Remediation progress: {ctx.remediation_progress}", body))

    sev_parts = [f"{k}: {v}" for k, v in sorted(ctx.severity_breakdown.items())]
    story.append(_p(f"Event severity breakdown: {', '.join(sev_parts) or 'none'}", body))
    story.append(
        _p(
            f"Affected source IPs: {', '.join(ctx.affected_source_ips) or 'none'} · "
            f"Destinations: {', '.join(ctx.affected_destinations) or 'none'}",
            body,
        )
    )

    corr = ctx.correlation_summary
    story.append(
        _p(
            f"Correlation summary: {corr.get('alert_count', 0)} alert(s), "
            f"{corr.get('correlated_event_count', 0)} correlated event(s), "
            f"rules: {', '.join(corr.get('rule_families') or []) or 'none'}",
            body,
        )
    )

    if ctx.attack_timeline:
        story.append(Paragraph("Attack timeline (deterministic)", h2))
        hdr = ["Phase", "Timestamp (UTC)", "Detail"]
        rows = [hdr]
        for item in ctx.attack_timeline[:12]:
            rows.append([item.get("phase", ""), item.get("timestamp", ""), item.get("detail", "")])
        tbl = Table(rows, colWidths=[1.2 * inch, 2.0 * inch, 3.3 * inch])
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#334155")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(tbl)
        story.append(Spacer(1, 8))
        story.append(_p(f"First event: {ctx.first_event_at or 'N/A'} · Last: {ctx.last_event_at or 'N/A'}", meta))


def _render_ai_narrative(story: list, incident: Incident, h2, body) -> None:
    """Append AI narrative sections, clearly separated from deterministic data."""
    story.append(Paragraph("AI narrative (advisory)", h2))
    story.append(
        _p(
            "The sections below are AI-generated recommendations grounded in linked telemetry. "
            "Deterministic metrics and charts above remain the authoritative SOC record.",
            body,
        )
    )
    story.append(Paragraph("Executive summary", h2))
    story.append(_p(incident.ai_summary or "N/A — run AI analysis to populate.", body))
    notes = incident.analyst_notes or ""
    if notes:
        story.append(Paragraph("Analysis notes", h2))
        story.append(_p(notes, body))
    story.append(Paragraph("Remediation", h2))
    story.append(_p(incident.remediation or "N/A", body))


def build_incident_pdf(incident: Incident, path: Path, db=None) -> str:
    ensure_reports_dir()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CGTitle",
        parent=styles["Heading1"],
        fontSize=20,
        spaceAfter=12,
        textColor=colors.HexColor("#0ea5e9"),
    )
    h2 = ParagraphStyle("CGH2", parent=styles["Heading2"], fontSize=12, spaceBefore=14, spaceAfter=8)
    body = ParagraphStyle("CGBody", parent=styles["Normal"], fontSize=9, leading=12)
    caption_style = ParagraphStyle(
        "CGCaption",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=10,
    )
    meta = ParagraphStyle("CGMeta", parent=styles["Normal"], fontSize=8, textColor=colors.grey, leading=11)

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        title=f"Incident {incident.id}",
        leftMargin=48,
        rightMargin=48,
        topMargin=48,
        bottomMargin=48,
    )
    story: list = []
    band = _severity_band_color(incident.severity)
    story.append(
        Table(
            [[""]],
            colWidths=[7 * inch],
            rowHeights=[0.12 * inch],
            style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), band), ("LEFTPADDING", (0, 0), (-1, -1), 0)]),
        )
    )
    story.append(Spacer(1, 14))
    story.append(Paragraph("CyberGuard AI", title_style))
    story.append(_p("Incident report", styles["Heading2"]))
    story.append(
        _p(
            f"Generated {datetime.now(timezone.utc).isoformat()} · Incident #{incident.id}",
            meta,
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(f"<b>Title:</b> {escape(incident.title or '—')}", body),
    )
    story.append(
        Paragraph(
            f"<b>Severity:</b> {escape(incident.severity.value)} · "
            f"<b>Status:</b> {escape(incident.status.value.replace('_', ' '))} · "
            f"<b>Created:</b> {escape(incident.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if incident.created_at else '—')}",
            body,
        ),
    )
    story.append(Spacer(1, 10))
    story.append(Paragraph("Summary", h2))
    story.append(_p(incident.summary or "—", body))

    evs = list(incident.events or [])
    ctx = build_incident_report_context(db, incident) if db is not None else None
    if ctx is None:
        ctx = IncidentReportContext(
            incident_status=incident.status.value.replace("_", " "),
            severity_breakdown={incident.severity.value: len(evs)} if evs else {},
            mtta_seconds=None,
            mttr_seconds=None,
            affected_source_ips=sorted({e.source_ip for e in evs if e.source_ip}),
            affected_destinations=sorted({e.destination_ip for e in evs if e.destination_ip}),
            attack_timeline=[],
            correlation_summary={
                "alert_count": 0,
                "correlated_event_count": 0,
                "rule_families": [],
                "attack_types": [],
            },
            remediation_progress="Unknown — database session not provided.",
            event_count=len(evs),
            first_event_at=None,
            last_event_at=None,
        )
    _render_deterministic_context(story, ctx, h2, body, meta)
    _render_ai_narrative(story, incident, h2, body)
    ai_rows = _incident_ai_classification_rows(evs)
    if ai_rows:
        story.append(Paragraph("AI Detection Copilot", h2))
        story.append(
            _p(
                "Event-level AI classifications are recommendations only; rule severity remains the official SOC severity.",
                body,
            )
        )
        data_ai = [["Event", "Attack type", "Confidence", "Suggested severity", "Why classified"], *ai_rows[:12]]
        ai_table = Table(data_ai, colWidths=[0.55 * inch, 1.15 * inch, 0.75 * inch, 0.95 * inch, 3.1 * inch])
        ai_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#155e75")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#334155")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ecfeff"), colors.HexColor("#f8fafc")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(ai_table)

    charts = _incident_event_charts(evs, incident.title or "")
    if charts:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Visual analytics (Plotly)", h2))
        for buf, cap in charts:
            story.append(Image(buf, width=6.2 * inch, height=2.65 * inch))
            story.append(_p(cap, caption_style))

    story.append(Spacer(1, 14))
    story.append(Paragraph("Related events", h2))
    hdr = ["Time (UTC)", "Type", "Source", "Port", "Message"]
    data = [hdr]
    for ev in evs[:40]:
        ts = ev.timestamp.strftime("%Y-%m-%d %H:%M") if ev.timestamp else ""
        msg = (ev.message or ev.raw_log or "")[:56]
        port = str(ev.port) if ev.port is not None else "—"
        data.append([ts, ev.event_type[:14], (ev.source_ip or "—")[:18], port, msg])

    if len(data) == 1:
        data.append(["—", "—", "—", "—", "No linked events"])

    t = Table(data, colWidths=[1.15 * inch, 1.0 * inch, 1.05 * inch, 0.45 * inch, 2.85 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0c4a6e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ALIGN", (3, 0), (3, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#334155")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#f1f5f9")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(t)
    if len(evs) > 40:
        story.append(Spacer(1, 6))
        story.append(_p(f"… {len(evs) - 40} additional events not shown.", meta))

    doc.build(story)
    return str(path)


def _alert_portfolio_charts(ctx: dict) -> list[tuple[io.BytesIO, str]]:
    """Build chart PNG buffers for alert portfolio PDF."""
    out: list[tuple[io.BytesIO, str]] = []
    sev_map = ctx.get("severity_counts") or {}
    if sev_map:
        names = [s.value for s in _severity_order()]
        vals = [int(sev_map.get(s.value, 0)) for s in _severity_order()]
        fig = go.Figure(
            data=[
                go.Bar(
                    x=names,
                    y=vals,
                    marker=dict(
                        color=["#3b82f6", "#eab308", "#f97316", "#dc2626"],
                        line=dict(color="#1e293b", width=1),
                    ),
                )
            ]
        )
        fig.update_layout(
            title=dict(text="Alerts by severity", font=dict(color="#f1f5f9", size=15)),
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            font=dict(color="#e2e8f0", size=10),
            margin=dict(l=12, r=12, t=44, b=40),
            height=280,
            width=760,
        )
        buf = _plotly_fig_to_png(fig, width=760, height=280)
        if buf:
            out.append((buf, "Severity mix shows where triage effort should concentrate."))

    status_map = ctx.get("status_counts") or {}
    if status_map:
        labels = list(status_map.keys())
        vals = [int(status_map[k]) for k in labels]
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=vals,
                    hole=0.45,
                    marker=dict(colors=["#38bdf8", "#a78bfa", "#34d399", "#64748b"]),
                )
            ]
        )
        fig.update_layout(
            title=dict(text="Triage status", font=dict(color="#f1f5f9", size=15)),
            paper_bgcolor="#0f172a",
            font=dict(color="#e2e8f0", size=10),
            margin=dict(l=8, r=8, t=44, b=8),
            height=280,
            width=760,
        )
        buf = _plotly_fig_to_png(fig, width=760, height=280)
        if buf:
            out.append((buf, "Open vs acknowledged vs resolved alerts in this export."))

    rule_map = ctx.get("rule_counts") or {}
    if rule_map:
        items = list(rule_map.items())[:10]
        labels = [k[:28] for k, _ in items]
        vals = [v for _, v in items]
        fig = go.Figure(
            data=[
                go.Bar(
                    x=vals,
                    y=labels,
                    orientation="h",
                    marker=dict(color="#0ea5e9", line=dict(color="#1e293b", width=1)),
                )
            ]
        )
        fig.update_layout(
            title=dict(text="Top detection rules", font=dict(color="#f1f5f9", size=15)),
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            font=dict(color="#e2e8f0", size=10),
            margin=dict(l=120, r=12, t=44, b=40),
            height=max(280, 40 + len(labels) * 28),
            width=760,
        )
        buf = _plotly_fig_to_png(fig, width=760, height=max(280, 40 + len(labels) * 28))
        if buf:
            out.append((buf, "Which rules fired most often in the filtered alert set."))

    day_map = ctx.get("day_buckets") or {}
    if len(day_map) >= 2:
        days = list(day_map.keys())
        vals = [int(day_map[d]) for d in days]
        fig = go.Figure(
            data=[go.Scatter(x=days, y=vals, mode="lines+markers", line=dict(color="#22d3ee", width=2))]
        )
        fig.update_layout(
            title=dict(text="Alert volume timeline", font=dict(color="#f1f5f9", size=15)),
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            font=dict(color="#e2e8f0", size=10),
            margin=dict(l=12, r=12, t=44, b=56),
            xaxis=dict(title="Date (UTC)", tickangle=-35, gridcolor="#334155"),
            yaxis=dict(title="Alerts", gridcolor="#334155"),
            height=300,
            width=760,
        )
        buf = _plotly_fig_to_png(fig, width=760, height=300)
        if buf:
            out.append((buf, "Daily alert cadence — spikes often correlate with range lab runs or ingest bursts."))

    ip_map = ctx.get("source_ip_counts") or {}
    if ip_map:
        items = list(ip_map.items())[:8]
        labels = [k for k, _ in items]
        vals = [v for _, v in items]
        fig = go.Figure(
            data=[
                go.Bar(
                    x=labels,
                    y=vals,
                    marker=dict(color="#f97316", line=dict(color="#1e293b", width=1)),
                )
            ]
        )
        fig.update_layout(
            title=dict(text="Top source IPs", font=dict(color="#f1f5f9", size=15)),
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            font=dict(color="#e2e8f0", size=10),
            margin=dict(l=12, r=12, t=44, b=48),
            xaxis=dict(title="Source IP", gridcolor="#334155"),
            yaxis=dict(title="Alerts", gridcolor="#334155"),
            height=280,
            width=760,
        )
        buf = _plotly_fig_to_png(fig, width=760, height=280)
        if buf:
            out.append(
                (
                    buf,
                    "Attacker origin IPs from linked events — device launches should show your workstation IP.",
                )
            )

    return out


def build_alerts_portfolio_pdf(ctx: dict, path: Path) -> str:
    """Export filtered alert portfolio with charts, KPIs, and summary tables."""
    from app.services.chart_render import alert_portfolio_charts

    ensure_reports_dir()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "AlertTitle",
        parent=styles["Heading1"],
        fontSize=20,
        spaceAfter=12,
        textColor=colors.HexColor("#0ea5e9"),
    )
    h2 = ParagraphStyle("AlertH2", parent=styles["Heading2"], fontSize=12, spaceBefore=14, spaceAfter=8)
    body = ParagraphStyle("AlertBody", parent=styles["Normal"], fontSize=9, leading=12)
    caption_style = ParagraphStyle(
        "AlertCap",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=10,
    )
    meta = ParagraphStyle("AlertMeta", parent=styles["Normal"], fontSize=8, textColor=colors.grey, leading=11)
    callout = ParagraphStyle(
        "AlertCallout",
        parent=body,
        backColor=colors.HexColor("#f0f9ff"),
        borderColor=colors.HexColor("#0ea5e9"),
        borderWidth=1,
        borderPadding=8,
        spaceBefore=6,
        spaceAfter=12,
    )

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        title="CyberGuard alerts portfolio",
        leftMargin=48,
        rightMargin=48,
        topMargin=48,
        bottomMargin=48,
    )
    story: list = []

    # Brand header band
    story.append(
        Table(
            [[""]],
            colWidths=[7 * inch],
            rowHeights=[0.12 * inch],
            style=TableStyle(
                [("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0ea5e9")), ("LEFTPADDING", (0, 0), (-1, -1), 0)]
            ),
        )
    )
    story.append(Spacer(1, 14))
    story.append(Paragraph("CyberGuard AI", title_style))
    story.append(_p("Alert portfolio report", styles["Heading2"]))
    story.append(
        _p(
            f"Generated {ctx.get('generated_at', datetime.now(timezone.utc).isoformat())} · "
            f"Filter: {ctx.get('filter_label', 'all alerts')}",
            meta,
        )
    )
    story.append(
        _p(
            f"Observation window: {ctx.get('date_range', '—')} · "
            f"Unique source IPs: {ctx.get('unique_source_ips', 0)} · "
            f"Resolved: {ctx.get('resolved_count', 0)}",
            meta,
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Executive summary", h2))
    story.append(_p(ctx.get("executive_summary") or "—", callout))

    charts = alert_portfolio_charts(ctx)
    if charts:
        story.append(Paragraph("Visual analytics", h2))
        story.append(
            _p(
                "Charts below summarize severity, workflow, temporal patterns, detection rules, "
                "MITRE mapping, and attacker origin for the exported alert set.",
                body,
            )
        )
        chart_width = 6.35 * inch
        idx = 0
        while idx < len(charts):
            buf_a, cap_a, height_a = charts[idx]
            # Pair severity + status side-by-side when two consecutive charts fit
            if idx + 1 < len(charts) and height_a >= 2.0:
                buf_b, cap_b, height_b = charts[idx + 1]
                if height_b >= 2.0:
                    pair_w = chart_width / 2 - 0.08 * inch
                    pair_h = min(height_a, height_b) * inch * 0.98
                    story.append(
                        Table(
                            [
                                [
                                    Image(buf_a, width=pair_w, height=pair_h),
                                    Image(buf_b, width=pair_w, height=pair_h),
                                ]
                            ],
                            colWidths=[chart_width / 2, chart_width / 2],
                        )
                    )
                    story.append(_p(f"{cap_a} {cap_b}", caption_style))
                    idx += 2
                    continue
            story.append(Image(buf_a, width=chart_width, height=height_a * inch))
            story.append(_p(cap_a, caption_style))
            idx += 1

    attack_map = ctx.get("attack_counts") or {}
    mitre_map = ctx.get("mitre_counts") or {}
    if attack_map or mitre_map:
        story.append(Paragraph("Threat intelligence summary", h2))

    if attack_map:
        atk_rows = [["Attack type", "Alerts", "Share"]] + [
            [
                k,
                str(v),
                f"{(100 * v / max(int(ctx.get('total_alerts') or 1), 1)):.0f}%",
            ]
            for k, v in attack_map.items()
        ]
        atk_tbl = Table(atk_rows, colWidths=[3.8 * inch, 1.0 * inch, 1.2 * inch])
        atk_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0c4a6e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#334155")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#f1f5f9")]),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(Paragraph("Attack types (AI Copilot)", styles["Heading3"]))
        story.append(atk_tbl)
        story.append(Spacer(1, 10))

    if mitre_map:
        mitre_rows = [["MITRE technique", "Alert hits", "Share"]] + [
            [
                k,
                str(v),
                f"{(100 * v / max(int(ctx.get('total_alerts') or 1), 1)):.0f}%",
            ]
            for k, v in mitre_map.items()
        ]
        mitre_tbl = Table(mitre_rows, colWidths=[2.2 * inch, 1.2 * inch, 1.2 * inch])
        mitre_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#312e81")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#334155")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#faf5ff"), colors.HexColor("#f8fafc")]),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(Paragraph("MITRE ATT&CK techniques", styles["Heading3"]))
        story.append(mitre_tbl)
        story.append(Spacer(1, 10))

    story.append(Paragraph("Alert inventory", h2))
    hdr = ["ID", "Sev", "Status", "Rule", "Source IP", "Ev", "Triggered", "Title"]
    rows = [hdr]
    for row in ctx.get("alert_rows") or []:
        rows.append(
            [
                row.get("id", ""),
                row.get("severity", ""),
                row.get("status", ""),
                row.get("rule", ""),
                row.get("source_ip", ""),
                row.get("events", ""),
                row.get("triggered", ""),
                row.get("title", ""),
            ]
        )
    if len(rows) == 1:
        rows.append(["—", "—", "—", "—", "—", "—", "—", "No alerts"])

    tbl = Table(
        rows,
        colWidths=[0.35 * inch, 0.5 * inch, 0.65 * inch, 0.85 * inch, 0.85 * inch, 0.35 * inch, 0.95 * inch, 2.4 * inch],
    )
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0c4a6e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#334155")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#f1f5f9")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(tbl)
    total = int(ctx.get("total_alerts") or 0)
    shown = len(ctx.get("alert_rows") or [])
    if total > shown:
        story.append(Spacer(1, 6))
        story.append(_p(f"… {total - shown} additional alerts not listed (export cap {shown}).", meta))

    story.append(Spacer(1, 8))
    story.append(
        _p(
            "CyberGuard AI — deterministic alert portfolio. Charts and tables reflect the filter "
            "applied at export time; re-generate after triage for an updated snapshot.",
            meta,
        )
    )

    doc.build(story)
    return str(path)


def _severity_order() -> list[Severity]:
    return [Severity.low, Severity.medium, Severity.high, Severity.critical]


def _severity_at_least(sev: Severity, minimum: Severity) -> bool:
    order = {s: i for i, s in enumerate(_severity_order())}
    return order[sev] >= order[minimum]


def incidents_matching_digest_min_severity(incidents: list[Incident], min_severity: Severity) -> list[Incident]:
    return [i for i in incidents if _severity_at_least(i.severity, min_severity)]


def digest_severity_filter_label(min_severity: Severity) -> str:
    if min_severity == Severity.low:
        return "all severities"
    if min_severity == Severity.medium:
        return "medium and above (medium, high, critical)"
    if min_severity == Severity.high:
        return "high and above (high, critical)"
    return "critical only"


def build_digest_pdf(
    *,
    path: Path,
    window_start: datetime,
    window_end: datetime,
    min_severity: Severity,
    incidents: list[Incident],
    events_count: int,
    alerts_count: int,
) -> str:
    """Aggregate SOC digest for scheduled email reports."""
    ensure_reports_dir()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DigestTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=10,
        textColor=colors.HexColor("#0ea5e9"),
    )
    h2 = ParagraphStyle("DigestH2", parent=styles["Heading2"], fontSize=11, spaceBefore=12, spaceAfter=6)
    body = ParagraphStyle("DigestBody", parent=styles["Normal"], fontSize=9, leading=12)
    caption_style = ParagraphStyle(
        "DigestCap",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=8,
    )
    meta = ParagraphStyle("DigestMeta", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    filtered = incidents_matching_digest_min_severity(incidents, min_severity)
    sev_counts = Counter(i.severity for i in filtered)

    chart_buf, chart_caption = _digest_severity_chart_png(min_severity, sev_counts)

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        title="CyberGuard digest",
        leftMargin=48,
        rightMargin=48,
        topMargin=48,
        bottomMargin=48,
    )
    story: list = [
        Paragraph("CyberGuard AI", title_style),
        _p("Scheduled security digest", styles["Heading2"]),
        _p(
            f"Window: {window_start.isoformat()} → {window_end.isoformat()} (UTC) · "
            f"Severity filter: {digest_severity_filter_label(min_severity)}",
            meta,
        ),
        _p(
            "The filter is a minimum threshold: incidents at that level or higher are included. "
            'Seeing only “high” rows with a medium filter is normal if no medium or critical incidents occurred in the window.',
            body,
        ),
        _p(
            f"Totals in window: {events_count} events ingested, {alerts_count} alerts, "
            f"{len(filtered)} incidents matching the severity filter.",
            body,
        ),
        Spacer(1, 10),
    ]
    if chart_buf:
        story.append(Image(chart_buf, width=5.5 * inch, height=2.2 * inch))
        story.append(_p(chart_caption, caption_style))
    story.extend([Spacer(1, 12), Paragraph("Incidents", h2)])

    hdr = ["ID", "Severity", "Status", "Title"]
    rows = [hdr]
    for inc in filtered[:50]:
        rows.append(
            [
                str(inc.id),
                inc.severity.value,
                inc.status.value.replace("_", " "),
                (inc.title or "")[:52],
            ]
        )
    if len(rows) == 1:
        rows.append(["—", "—", "—", "No incidents in this window"])

    tbl = Table(rows, colWidths=[0.45 * inch, 0.75 * inch, 0.95 * inch, 4.85 * inch])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0c4a6e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#334155")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#f1f5f9")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(tbl)
    if len(filtered) > 50:
        story.append(Spacer(1, 6))
        story.append(_p(f"… {len(filtered) - 50} more incidents not listed.", meta))

    doc.build(story)
    return str(path)
