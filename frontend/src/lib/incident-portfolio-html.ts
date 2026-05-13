import type { IncidentPortfolioReport } from "@/lib/api/types";

function escapeHtml(text: string): string {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function maxFromPairs(rows: string[][], valueCol = 1): number {
  const nums = rows.map((r) => Number.parseInt(r[valueCol] ?? "0", 10)).filter((n) => !Number.isNaN(n));
  return Math.max(1, ...nums, 1);
}

function barBlock(title: string, rows: string[][], valueIdx = 1): string {
  if (!rows.length) {
    return `<section class="panel"><h2 class="panel-title">${escapeHtml(title)}</h2><p class="muted">No data in this range.</p></section>`;
  }
  const max = maxFromPairs(rows, valueIdx);
  const bars = rows
    .map(([label, val]) => {
      const n = Number.parseInt(val, 10) || 0;
      const pct = Math.round((n / max) * 100);
      return `<div class="bar-row">
  <span class="bar-label">${escapeHtml(label)}</span>
  <div class="bar-track" role="presentation"><span class="bar-fill" style="width:${pct}%"></span></div>
  <span class="bar-val">${escapeHtml(val)}</span>
</div>`;
    })
    .join("");
  return `<section class="panel"><h2 class="panel-title">${escapeHtml(title)}</h2><div class="bar-stack">${bars}</div></section>`;
}

function styledTable(title: string, headers: string[], rows: string[][]): string {
  if (!rows.length) {
    return `<section class="panel"><h2 class="panel-title">${escapeHtml(title)}</h2><p class="muted">No rows.</p></section>`;
  }
  const th = headers
    .map((h) => `<th scope="col">${escapeHtml(h)}</th>`)
    .join("");
  const trs = rows
    .map(
      (r) =>
        `<tr>${r.map((c, i) => `<td${i === 0 && headers[0] === "ID" ? ' class="mono"' : ""}>${escapeHtml(c)}</td>`).join("")}</tr>`,
    )
    .join("");
  return `<section class="panel">
  <h2 class="panel-title">${escapeHtml(title)}</h2>
  <div class="table-wrap">
    <table class="data-table">
      <thead><tr>${th}</tr></thead>
      <tbody>${trs}</tbody>
    </table>
  </div>
</section>`;
}

function listBlock(title: string, items: string[]): string {
  if (!items.length) return "";
  const lis = items.map((x) => `<li>${escapeHtml(x)}</li>`).join("");
  return `<section class="panel panel--prose">
  <h2 class="panel-title">${escapeHtml(title)}</h2>
  <ul class="prose-list">${lis}</ul>
</section>`;
}

function formatFilters(f: IncidentPortfolioReport["filters"]): string {
  const sev = f.severity ?? "all";
  const st = f.status ?? "all";
  const q = (f.q ?? "").trim() || "—";
  return `<div class="pill-row">
  <span class="pill"><span class="pill-k">Severity</span> ${escapeHtml(sev)}</span>
  <span class="pill"><span class="pill-k">Status</span> ${escapeHtml(st)}</span>
  <span class="pill"><span class="pill-k">Search</span> ${escapeHtml(q)}</span>
</div>`;
}

/** Self-contained HTML for download / print — dark SOC report, bars + refined tables. */
export function buildIncidentPortfolioHtml(report: IncidentPortfolioReport): string {
  const { generated_at, filters, stats, charts, ai, ai_error, truncation_note, truncated } = report;
  const total = String((stats.total_matching as number) ?? 0);
  const sample = String((stats.sample_size as number) ?? 0);
  const sevRows = charts.severity_bar.map((r) => [r.name, String(r.count)]);
  const stRows = charts.status_bar.map((r) => [r.name, String(r.count)]);
  const weekRows = charts.weekly_line.map((r) => [r.week_start.slice(0, 10), String(r.count)]);
  const ruleRows = charts.rules_bar.map((r) => [r.rule_name, String(r.count)]);
  const mitreRows = charts.mitre_bar.map((r) => [r.technique_id, r.label, String(r.count)]);

  const oldest = (stats.oldest_open as Array<{ id: number; title: string; days_open: number }>) ?? [];
  const oldRows = oldest.map((o) => [String(o.id), o.title, String(o.days_open)]);

  const aiHtml = ai
    ? `<section class="panel panel--hero">
  <p class="eyebrow">AI narrative</p>
  <p class="lead">${escapeHtml(ai.executive_summary)}</p>
  ${listBlock("Key findings", ai.key_findings)}
  ${listBlock("Risks", ai.risks)}
  ${listBlock("Recommendations", ai.recommendations)}
  ${listBlock("Themes", ai.themes)}
</section>`
    : "";

  const warn = ai_error
    ? `<div class="callout callout--warn" role="status">${escapeHtml(ai_error)}</div>`
    : "";
  const trunc =
    truncated && truncation_note
      ? `<div class="callout callout--muted">${escapeHtml(truncation_note)}</div>`
      : "";

  const spike = stats.spike_last_period ? `<p class="spike-tag">Volume spike flagged in latest period vs prior weeks.</p>` : "";

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CyberGuard — Incident portfolio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    :root {
      --bg: #07080c;
      --surface: #0f1118;
      --surface2: #141824;
      --border: rgba(148, 163, 184, 0.12);
      --text: #e8eaef;
      --muted: #94a3b8;
      --accent: #22d3ee;
      --accent-dim: rgba(34, 211, 238, 0.35);
      --violet: #a78bfa;
      --warn-bg: rgba(251, 191, 36, 0.08);
      --warn-border: rgba(251, 191, 36, 0.35);
      --warn-text: #fcd34d;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "DM Sans", system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      font-size: 15px;
      line-height: 1.55;
      min-height: 100vh;
    }
    .mesh {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      background:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(34, 211, 238, 0.12), transparent 55%),
        radial-gradient(ellipse 60% 40% at 100% 0%, rgba(167, 139, 250, 0.1), transparent 50%),
        var(--bg);
    }
    .wrap {
      position: relative;
      z-index: 1;
      max-width: 920px;
      margin: 0 auto;
      padding: 48px 28px 64px;
    }
    .doc-header {
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 28px 28px 24px;
      background: linear-gradient(145deg, var(--surface) 0%, var(--surface2) 100%);
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.45);
    }
    .brand {
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 12px;
    }
    h1 {
      font-size: clamp(1.65rem, 4vw, 2.1rem);
      font-weight: 700;
      letter-spacing: -0.03em;
      margin: 0 0 8px;
      line-height: 1.15;
    }
    .sub {
      color: var(--muted);
      font-size: 14px;
      margin: 0 0 20px;
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
      margin-top: 8px;
    }
    .kpi {
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 16px;
      background: rgba(15, 17, 24, 0.6);
    }
    .kpi .kpi-num {
      display: block;
      font-size: 1.65rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #fff;
    }
    .kpi span {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }
    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 16px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 999px;
      border: 1px solid var(--border);
      font-size: 13px;
      background: rgba(0, 0, 0, 0.25);
    }
    .pill-k { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; }
    .callout {
      margin: 20px 0 0;
      padding: 14px 16px;
      border-radius: 12px;
      font-size: 14px;
      border: 1px solid var(--border);
    }
    .callout--warn {
      background: var(--warn-bg);
      border-color: var(--warn-border);
      color: var(--warn-text);
    }
    .callout--muted { color: var(--muted); background: rgba(148, 163, 184, 0.06); }
    .spike-tag {
      margin: 12px 0 0;
      font-size: 13px;
      color: var(--violet);
    }
    .panel {
      margin-top: 28px;
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 22px 24px;
      background: rgba(15, 17, 24, 0.85);
      backdrop-filter: blur(8px);
    }
    .panel--hero { border-color: rgba(34, 211, 238, 0.2); background: linear-gradient(160deg, rgba(34, 211, 238, 0.06), rgba(15, 17, 24, 0.95)); }
    .panel--prose .panel-title { margin-bottom: 12px; }
    .panel-title {
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--muted);
      margin: 0 0 16px;
    }
    .eyebrow { font-size: 12px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--accent); margin: 0 0 8px; }
    .lead { font-size: 1.05rem; line-height: 1.65; margin: 0 0 20px; color: #f1f5f9; }
    .bar-stack { display: flex; flex-direction: column; gap: 12px; }
    .bar-row {
      display: grid;
      grid-template-columns: minmax(100px, 1fr) minmax(120px, 3fr) 48px;
      align-items: center;
      gap: 12px;
    }
    .bar-label { font-size: 14px; color: #cbd5e1; text-transform: capitalize; }
    .bar-track {
      height: 10px;
      border-radius: 999px;
      background: rgba(148, 163, 184, 0.12);
      overflow: hidden;
    }
    .bar-fill {
      display: block;
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--accent-dim), var(--accent));
      box-shadow: 0 0 20px rgba(34, 211, 238, 0.25);
    }
    .bar-val { font-family: "JetBrains Mono", monospace; font-size: 13px; text-align: right; color: var(--accent); }
    .table-wrap { overflow-x: auto; margin: 0 -4px; }
    .data-table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      font-size: 14px;
    }
    .data-table th {
      text-align: left;
      padding: 10px 12px;
      color: var(--muted);
      font-weight: 600;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      border-bottom: 1px solid var(--border);
    }
    .data-table td {
      padding: 12px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.08);
      vertical-align: top;
    }
    .data-table tbody tr:hover td { background: rgba(34, 211, 238, 0.04); }
    .data-table .mono { font-family: "JetBrains Mono", monospace; font-size: 13px; color: var(--accent); }
    .prose-list { margin: 0; padding-left: 1.15rem; }
    .prose-list li { margin: 8px 0; color: #e2e8f0; }
    footer {
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid var(--border);
      font-size: 12px;
      color: var(--muted);
      text-align: center;
    }
    @media print {
      .mesh { display: none; }
      body { background: #fff; color: #0f172a; }
      .doc-header, .panel { box-shadow: none; border-color: #cbd5e1; background: #fff; }
      .bar-fill { background: #0891b2; box-shadow: none; }
      .pill, .kpi { border-color: #e2e8f0; }
      .data-table th { color: #475569; }
      .data-table td { border-color: #e2e8f0; }
      .bar-label, .lead, .data-table td { color: #1e293b; }
      .brand, .bar-val, .mono { color: #0e7490; }
    }
  </style>
</head>
<body>
  <div class="mesh" aria-hidden="true"></div>
  <div class="wrap">
    <header class="doc-header">
      <p class="brand">CyberGuard / portfolio intelligence</p>
      <h1>Incident portfolio report</h1>
      <p class="sub">Generated <strong style="color:#e2e8f0">${escapeHtml(generated_at)}</strong> — statistics are deterministic; AI sections are advisory.</p>
      <div class="kpi-grid">
        <div class="kpi"><span class="kpi-num">${escapeHtml(total)}</span><span>Matching incidents</span></div>
        <div class="kpi"><span class="kpi-num">${escapeHtml(sample)}</span><span>Sample analyzed (rules / MITRE)</span></div>
      </div>
      ${formatFilters(filters)}
      ${warn}
      ${trunc}
      ${spike}
    </header>

    ${barBlock("Severity distribution", sevRows)}
    ${barBlock("Status distribution", stRows)}
    ${barBlock("Incidents created by week (UTC)", weekRows)}
    ${barBlock("Top detection rules (sample cap)", ruleRows)}
    ${styledTable("MITRE techniques (weighted)", ["ID", "Technique", "Weight"], mitreRows)}
    ${styledTable("Oldest open backlog", ["ID", "Title", "Days open"], oldRows)}

    ${aiHtml}

    <footer>CyberGuard AI — export mirrors in-app aggregates. Open the HTML in a browser to print if needed.</footer>
  </div>
</body>
</html>`;
}

export function downloadIncidentPortfolioHtml(report: IncidentPortfolioReport, filename?: string): void {
  const html = buildIncidentPortfolioHtml(report);
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename ?? `incident-portfolio-${report.generated_at.slice(0, 10)}.html`;
  a.click();
  URL.revokeObjectURL(url);
}
