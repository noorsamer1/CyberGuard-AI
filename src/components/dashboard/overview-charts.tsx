"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DashboardCharts as ChartsData } from "@/lib/api/types";

export function OverviewCharts({ data }: { data: ChartsData }) {
  const attackTimeline = (data.attack_timeline ?? []).map((point) => ({
    bucket: new Date(point.bucket).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit" }),
    events: point.events,
    alerts: point.alerts,
    incidents: point.incidents,
  }));
  const topRules = (data.top_rules_24h ?? []).map((item) => ({
    rule: item.rule_name.length > 22 ? `${item.rule_name.slice(0, 20)}…` : item.rule_name,
    count: item.count,
  }));
  const topRisks = (data.top_risks ?? []).map((risk) => ({
    source: risk.source_ip,
    highCriticalEvents: risk.high_critical_events,
    alerts: risk.alerts,
  }));
  const mitreCoverage = (data.mitre_coverage ?? []).slice(0, 8).map((item) => ({
    technique: item.technique_id,
    count: item.count,
  }));
  const anomaly = data.anomaly_signals;
  const anomalySignals = [
    { label: "Exfil alerts", count: anomaly?.exfiltration_alerts ?? 0 },
    { label: "Auth anomalies", count: anomaly?.auth_anomaly_alerts ?? 0 },
    { label: "Outbound transfer", count: anomaly?.outbound_transfer_events ?? 0 },
    { label: "Privileged logins", count: anomaly?.privileged_login_events ?? 0 },
  ];
  const hasAnyChartData =
    attackTimeline.length > 0 ||
    topRules.length > 0 ||
    topRisks.length > 0 ||
    mitreCoverage.length > 0 ||
    anomalySignals.some((signal) => signal.count > 0);
  const timelineData =
    attackTimeline.length === 1
      ? [
          ...attackTimeline,
          {
            bucket: `${attackTimeline[0].bucket} +`,
            events: attackTimeline[0].events,
            alerts: attackTimeline[0].alerts,
            incidents: attackTimeline[0].incidents,
          },
        ]
      : attackTimeline;

  if (!hasAnyChartData) {
    return (
      <div className="rounded-xl border border-border/60 bg-card/40 p-6 backdrop-blur-sm">
        <p className="text-sm text-muted-foreground">
          No enriched dashboard chart data available yet for this window.
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-6">
      <div className="min-w-0 rounded-xl border border-border/60 bg-card/40 p-4 backdrop-blur-sm lg:col-span-4">
        <h3 className="mb-3 text-sm font-medium text-muted-foreground">
          Attack timeline (events, alerts, incidents)
        </h3>
        <div className="h-[220px] min-w-0">
          <ResponsiveContainer width="100%" height="100%" minWidth={280} minHeight={220}>
            <LineChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.35 0.02 260 / 0.5)" />
              <XAxis dataKey="bucket" tick={{ fill: "oklch(0.65 0.02 260)", fontSize: 11 }} />
              <YAxis tick={{ fill: "oklch(0.65 0.02 260)", fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: "oklch(0.2 0.02 260)",
                  border: "1px solid oklch(0.35 0.02 260)",
                  borderRadius: 8,
                }}
              />
              <Line type="monotone" dataKey="events" stroke="#22d3ee" strokeWidth={2} dot={{ r: 2 }} />
              <Line type="monotone" dataKey="alerts" stroke="#f97316" strokeWidth={2} dot={{ r: 2 }} />
              <Line type="monotone" dataKey="incidents" stroke="#ef4444" strokeWidth={2} dot={{ r: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="min-w-0 rounded-xl border border-border/60 bg-card/40 p-4 backdrop-blur-sm lg:col-span-2">
        <h3 className="mb-3 text-sm font-medium text-muted-foreground">Anomaly signals</h3>
        <div className="h-[220px] min-w-0">
          <ResponsiveContainer width="100%" height="100%" minWidth={240} minHeight={220}>
            <BarChart data={anomalySignals}>
              <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.35 0.02 260 / 0.5)" />
              <XAxis dataKey="label" tick={{ fill: "oklch(0.65 0.02 260)", fontSize: 10 }} />
              <YAxis tick={{ fill: "oklch(0.65 0.02 260)", fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: "oklch(0.2 0.02 260)",
                  border: "1px solid oklch(0.35 0.02 260)",
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="count" fill="#a78bfa" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="min-w-0 rounded-xl border border-border/60 bg-card/40 p-4 backdrop-blur-sm lg:col-span-3">
        <h3 className="mb-3 text-sm font-medium text-muted-foreground">Top triggered rules</h3>
        <div className="h-[220px] min-w-0">
          <ResponsiveContainer width="100%" height="100%" minWidth={280} minHeight={220}>
            <BarChart data={topRules} layout="vertical" margin={{ left: 12 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.35 0.02 260 / 0.5)" />
              <XAxis type="number" tick={{ fill: "oklch(0.65 0.02 260)", fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="rule"
                width={140}
                tick={{ fill: "oklch(0.65 0.02 260)", fontSize: 10 }}
              />
              <Tooltip
                contentStyle={{
                  background: "oklch(0.2 0.02 260)",
                  border: "1px solid oklch(0.35 0.02 260)",
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="count" fill="#22d3ee" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="min-w-0 rounded-xl border border-border/60 bg-card/40 p-4 backdrop-blur-sm lg:col-span-3">
        <h3 className="mb-3 text-sm font-medium text-muted-foreground">Top risky sources</h3>
        <div className="h-[200px] min-w-0">
          <ResponsiveContainer width="100%" height="100%" minWidth={280} minHeight={200}>
            <BarChart data={topRisks}>
              <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.35 0.02 260 / 0.5)" />
              <XAxis dataKey="source" tick={{ fill: "oklch(0.65 0.02 260)", fontSize: 10 }} />
              <YAxis
                tick={{ fill: "oklch(0.65 0.02 260)", fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{
                  background: "oklch(0.2 0.02 260)",
                  border: "1px solid oklch(0.35 0.02 260)",
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="highCriticalEvents" fill="#ef4444" radius={[4, 4, 0, 0]} />
              <Bar dataKey="alerts" fill="#f97316" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="min-w-0 rounded-xl border border-border/60 bg-card/40 p-4 backdrop-blur-sm lg:col-span-6">
        <h3 className="mb-3 text-sm font-medium text-muted-foreground">MITRE ATT&CK coverage (alerts)</h3>
        <div className="h-[180px] min-w-0">
          <ResponsiveContainer width="100%" height="100%" minWidth={320} minHeight={180}>
            <BarChart data={mitreCoverage} layout="vertical" margin={{ left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.35 0.02 260 / 0.5)" />
              <XAxis type="number" tick={{ fill: "oklch(0.65 0.02 260)", fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="technique"
                width={90}
                tick={{ fill: "oklch(0.65 0.02 260)", fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{
                  background: "oklch(0.2 0.02 260)",
                  border: "1px solid oklch(0.35 0.02 260)",
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="count" fill="#818cf8" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
