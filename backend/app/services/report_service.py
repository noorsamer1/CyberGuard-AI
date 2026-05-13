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


def build_incident_pdf(incident: Incident, path: Path) -> str:
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
    story.append(Paragraph("AI summary", h2))
    story.append(_p(incident.ai_summary or "N/A", body))
    story.append(Paragraph("Remediation", h2))
    story.append(_p(incident.remediation or "N/A", body))

    evs = list(incident.events or [])
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
