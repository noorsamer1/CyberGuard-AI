"""Headless chart PNG export for PDF reports (matplotlib — reliable in Docker)."""

from __future__ import annotations

import io
import logging
from collections.abc import Mapping, Sequence
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch

logger = logging.getLogger(__name__)

_SOC_BG = "#0f172a"
_SOC_GRID = "#334155"
_SOC_TEXT = "#e2e8f0"
_SOC_MUTED = "#94a3b8"
_SEVERITY_COLORS = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#ca8a04",
    "low": "#2563eb",
    "info": "#64748b",
}
_STATUS_COLORS = {
    "new": "#0ea5e9",
    "acknowledged": "#f59e0b",
    "resolved": "#22c55e",
    "false_positive": "#64748b",
    "unknown": "#94a3b8",
}


def _apply_soc_theme(fig: plt.Figure, ax: plt.Axes) -> None:
    """Apply CyberGuard dark SOC styling to a matplotlib axes."""
    fig.patch.set_facecolor(_SOC_BG)
    ax.set_facecolor(_SOC_BG)
    ax.tick_params(colors=_SOC_MUTED, labelsize=8)
    ax.xaxis.label.set_color(_SOC_TEXT)
    ax.yaxis.label.set_color(_SOC_TEXT)
    ax.title.set_color(_SOC_TEXT)
    for spine in ax.spines.values():
        spine.set_color(_SOC_GRID)


def _fig_to_png(fig: plt.Figure, dpi: int = 140) -> io.BytesIO | None:
    """Render figure to PNG bytes."""
    try:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor=_SOC_BG)
        buf.seek(0)
        return buf
    except Exception as exc:
        logger.warning("Matplotlib PNG export failed: %s", exc)
        return None
    finally:
        plt.close(fig)


def bar_chart(
    labels: Sequence[str],
    values: Sequence[int],
    *,
    title: str,
    color: str | None = None,
    horizontal: bool = False,
    color_map: Mapping[str, str] | None = None,
) -> io.BytesIO | None:
    """Bar chart (vertical or horizontal) with SOC theme."""
    if not labels or not values or sum(values) <= 0:
        return None
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    _apply_soc_theme(fig, ax)
    if color_map:
        bar_colors = [color_map.get(str(l).lower(), "#0ea5e9") for l in labels]
    else:
        bar_colors = color or "#0ea5e9"
    if horizontal:
        y_pos = range(len(labels))
        ax.barh(y_pos, values, color=bar_colors, height=0.55)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel("Count")
    else:
        ax.bar(labels, values, color=bar_colors, width=0.55)
        ax.set_ylabel("Count")
        plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    ax.grid(axis="y" if not horizontal else "x", color=_SOC_GRID, alpha=0.35, linestyle="--")
    return _fig_to_png(fig)


def donut_chart(
    labels: Sequence[str],
    values: Sequence[int],
    *,
    title: str,
    color_map: Mapping[str, str] | None = None,
) -> io.BytesIO | None:
    """Donut chart for categorical breakdown."""
    if not labels or not values or sum(values) <= 0:
        return None
    fig, ax = plt.subplots(figsize=(4.8, 3.4))
    _apply_soc_theme(fig, ax)
    if color_map:
        pie_colors = [color_map.get(str(l).lower(), "#0ea5e9") for l in labels]
    else:
        pie_colors = plt.cm.Set2.colors[: len(labels)]
    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,
        autopct=lambda pct: f"{pct:.0f}%" if pct >= 8 else "",
        startangle=90,
        colors=pie_colors,
        pctdistance=0.78,
        wedgeprops={"width": 0.42, "edgecolor": _SOC_BG, "linewidth": 1.5},
    )
    for t in autotexts:
        t.set_color(_SOC_TEXT)
        t.set_fontsize(7)
        t.set_fontweight("bold")
    ax.legend(
        wedges,
        [f"{l} ({v})" for l, v in zip(labels, values)],
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=7,
        frameon=False,
        labelcolor=_SOC_MUTED,
    )
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    return _fig_to_png(fig)


def line_timeline(
    labels: Sequence[str],
    values: Sequence[int],
    *,
    title: str,
) -> io.BytesIO | None:
    """Timeline line chart for alert volume over time."""
    if not labels or not values or sum(values) <= 0:
        return None
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    _apply_soc_theme(fig, ax)
    ax.fill_between(range(len(labels)), values, alpha=0.25, color="#0ea5e9")
    ax.plot(range(len(labels)), values, color="#0ea5e9", linewidth=2.2, marker="o", markersize=4)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=7)
    ax.set_ylabel("Alerts")
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    ax.grid(color=_SOC_GRID, alpha=0.35, linestyle="--")
    return _fig_to_png(fig)


def kpi_strip_png(metrics: list[tuple[str, str, str]]) -> io.BytesIO | None:
    """Render a row of KPI cards as a single PNG (label, value, accent hex)."""
    if not metrics:
        return None
    n = len(metrics)
    fig, axes = plt.subplots(1, n, figsize=(7.2, 1.35))
    fig.patch.set_facecolor(_SOC_BG)
    if n == 1:
        axes = [axes]
    for ax, (label, value, accent) in zip(axes, metrics):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        rect = FancyBboxPatch(
            (0.04, 0.08),
            0.92,
            0.84,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor="#1e293b",
            edgecolor=accent,
            linewidth=2,
        )
        ax.add_patch(rect)
        ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=16, fontweight="bold", color=_SOC_TEXT)
        ax.text(0.5, 0.28, label.upper(), ha="center", va="center", fontsize=7, color=_SOC_MUTED)
    return _fig_to_png(fig, dpi=120)


def alert_portfolio_charts(ctx: dict[str, Any]) -> list[tuple[io.BytesIO, str, float]]:
    """Build all alert portfolio chart PNGs with captions and height inches."""
    charts: list[tuple[io.BytesIO, str, float]] = []
    sev = ctx.get("severity_counts") or {}
    status = ctx.get("status_counts") or {}
    rules = ctx.get("rule_counts") or {}
    attacks = ctx.get("attack_counts") or {}
    mitre = ctx.get("mitre_counts") or {}
    sources = ctx.get("source_ip_counts") or {}
    timeline = ctx.get("timeline_buckets") or ctx.get("day_buckets") or {}

    kpi_metrics: list[tuple[str, str, str]] = [
        ("Total alerts", str(ctx.get("total_alerts", 0)), "#0ea5e9"),
        ("Correlated events", str(ctx.get("correlated_events", 0)), "#8b5cf6"),
        (
            "Critical + high",
            str(ctx.get("critical_high_count", 0)),
            "#dc2626",
        ),
        ("Open / new", str(ctx.get("open_count", 0)), "#f59e0b"),
    ]
    kpi_buf = kpi_strip_png(kpi_metrics)
    if kpi_buf:
        charts.append((kpi_buf, "Key metrics for the filtered alert set.", 1.05))

    if sev and sum(sev.values()) > 0:
        labels = list(sev.keys())
        values = [sev[k] for k in labels]
        buf = bar_chart(
            labels,
            values,
            title="Alerts by severity",
            color_map=_SEVERITY_COLORS,
        )
        if buf:
            charts.append((buf, "Severity distribution — prioritize critical and high first.", 2.55))

    if status and sum(status.values()) > 0:
        labels = list(status.keys())
        values = [status[k] for k in labels]
        buf = donut_chart(
            labels,
            values,
            title="Workflow status",
            color_map=_STATUS_COLORS,
        )
        if buf:
            charts.append((buf, "Analyst workflow load by alert status.", 2.55))

    if timeline and sum(timeline.values()) > 0:
        labels = sorted(timeline.keys())
        values = [timeline[k] for k in labels]
        buf = line_timeline(labels, values, title="Alert volume over time")
        if buf:
            charts.append((buf, "Temporal pattern — spikes may indicate coordinated activity.", 2.45))

    if rules:
        top = sorted(rules.items(), key=lambda x: -x[1])[:8]
        labels = [r[0][:28] for r, _ in top]
        values = [c for _, c in top]
        buf = bar_chart(labels, values, title="Top detection rules", horizontal=True, color="#38bdf8")
        if buf:
            charts.append((buf, "Rules firing most often in this export.", 2.65))

    if attacks:
        top = sorted(attacks.items(), key=lambda x: -x[1])[:8]
        labels = [a[0][:24] for a, _ in top]
        values = [c for _, c in top]
        buf = bar_chart(labels, values, title="Attack types (AI Copilot)", horizontal=True, color="#f97316")
        if buf:
            charts.append((buf, "AI-classified attack families across exported alerts.", 2.65))

    if mitre:
        top = sorted(mitre.items(), key=lambda x: -x[1])[:8]
        labels = [m[0][:20] for m, _ in top]
        values = [c for _, c in top]
        buf = bar_chart(labels, values, title="MITRE ATT&CK techniques", horizontal=True, color="#a78bfa")
        if buf:
            charts.append((buf, "Mapped techniques for threat-hunting and purple-team alignment.", 2.65))

    if sources:
        top = sorted(sources.items(), key=lambda x: -x[1])[:8]
        labels = [ip[:18] for ip, _ in top]
        values = [c for _, c in top]
        buf = bar_chart(labels, values, title="Top source IPs", horizontal=True, color="#34d399")
        if buf:
            charts.append((buf, "Source addresses to block, watch, or enrich in threat intel.", 2.65))

    return charts
