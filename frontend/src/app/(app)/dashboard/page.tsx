"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Clock3,
  CircleDot,
  FlaskConical,
  Gauge,
  Info,
  Radio,
  ShieldAlert,
  ShieldCheck,
  ShieldOff,
  Siren,
  FileWarning,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { OverviewCharts } from "@/components/dashboard/overview-charts";
import { SeverityBadge } from "@/components/common/severity-badge";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api/client";
import type {
  Alert,
  DashboardCharts,
  DashboardSummary,
  Severity,
  UIRecommendation,
} from "@/lib/api/types";

interface IncidentRow {
  id: number;
  title: string;
  severity: Severity;
  status: string;
  created_at: string;
}

export default function DashboardPage() {
  const [window, setWindow] = useState<"24h" | "7d" | "30d">("24h");
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["dashboard-summary", window],
    queryFn: () => apiFetch<DashboardSummary>(`/dashboard/summary?window=${window}`),
  });
  const { data: charts } = useQuery({
    queryKey: ["dashboard-charts", window],
    queryFn: () => apiFetch<DashboardCharts>(`/dashboard/charts?window=${window}`),
  });
  const { data: recentInc } = useQuery({
    queryKey: ["recent-incidents"],
    queryFn: () => apiFetch<IncidentRow[]>("/dashboard/recent-incidents"),
  });
  const { data: recentAlerts } = useQuery({
    queryKey: ["recent-alerts-dash"],
    queryFn: () => apiFetch<Alert[]>("/dashboard/recent-alerts"),
  });
  const { data: uiRecommendations } = useQuery({
    queryKey: ["dashboard-ui-recommendations"],
    queryFn: () => apiFetch<UIRecommendation[]>("/dashboard/ui-recommendations"),
  });

  const uiRecommendationsFiltered = useMemo(() => {
    const drop = new Set(["training-cadence", "learning-session", "low-training-cadence"]);
    return (uiRecommendations ?? []).filter(
      (r) =>
        !drop.has(r.id) &&
        !r.action_href.toLowerCase().includes("/learning") &&
        !r.action_href.toLowerCase().includes("/exercise"),
    );
  }, [uiRecommendations]);

  const workQueue = charts?.work_queue;
  const anomalySignals = charts?.anomaly_signals;
  const hasEnrichedDashboardPayload =
    !!charts && "attack_timeline" in charts && "work_queue" in charts && "anomaly_signals" in charts;

  const kpis: {
    label: string;
    value: string | number | undefined;
    icon: typeof Radio;
    hint?: string;
  }[] = [
    { label: "Open alerts", value: summary?.open_alerts ?? "—", icon: Radio },
    { label: "Critical open incidents", value: summary?.critical_open_incidents ?? "—", icon: ShieldAlert },
    {
      label: "MTTA (min)",
      value: summary?.mtta_minutes ?? "—",
      icon: Clock3,
      hint:
        "Mean Time To Acknowledge — average minutes from when an alert is created until an analyst acknowledges it in the selected time window. Lower is better for triage responsiveness.",
    },
    {
      label: "MTTR (min)",
      value: summary?.mttr_minutes ?? "—",
      icon: Gauge,
      hint:
        "Mean Time To Resolve — average minutes from open alert or incident to resolved or closed in the selected window. Tracks how quickly the team clears actionable work.",
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">SOC Operator Cockpit</h1>
          <p className="text-sm text-muted-foreground">
            Real-time triage posture, workload pressure, and attack progression.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={window} onValueChange={(value) => setWindow(value as "24h" | "7d" | "30d")}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7d</SelectItem>
              <SelectItem value="30d">Last 30d</SelectItem>
            </SelectContent>
          </Select>
          <Link href="/alerts" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
            Alert center
          </Link>
          <Link
            href="/incidents"
            className={cn(buttonVariants({ size: "sm" }), "bg-cyan-600 text-primary-foreground hover:bg-cyan-500")}
          >
            Incidents
          </Link>
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {summaryLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <Card key={i} className="border-border/60 bg-card/40 backdrop-blur-sm">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-4 rounded-sm" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16" />
                </CardContent>
              </Card>
            ))
          : kpis.map((k, i) => (
              <motion.div
                key={k.label}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <Card className="border-border/60 bg-card/40 backdrop-blur-sm">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <div className="flex min-w-0 flex-1 items-center gap-1.5">
                      <CardTitle className="truncate text-sm font-medium text-muted-foreground">{k.label}</CardTitle>
                      {k.hint ? (
                        <Tooltip>
                          <TooltipTrigger
                            render={
                              <button
                                type="button"
                                className="shrink-0 rounded p-0.5 text-muted-foreground transition-colors hover:text-cyan-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50"
                                aria-label={`What is ${k.label}?`}
                              >
                                <Info className="h-3.5 w-3.5" aria-hidden />
                              </button>
                            }
                          />
                          <TooltipContent side="top" align="start" className="max-w-[260px] text-left leading-relaxed">
                            {k.hint}
                          </TooltipContent>
                        </Tooltip>
                      ) : null}
                    </div>
                    <k.icon className="h-4 w-4 shrink-0 text-cyan-400" />
                  </CardHeader>
                  <CardContent>
                    <p className="text-2xl font-bold">{k.value}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
      </div>
      {!hasEnrichedDashboardPayload && (
        <Card className="border-amber-500/30 bg-amber-500/10">
          <CardContent className="pt-4">
            <p className="text-sm text-amber-300">
              Dashboard is running in compatibility mode. Core metrics are visible, but enriched charts/panels
              require the updated backend container. Rebuild backend and refresh.
            </p>
          </CardContent>
        </Card>
      )}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="border-border/60 bg-card/40">
          <CardHeader>
            <CardTitle className="text-base">Analyst work queue</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">New alerts</span>
              <span className="font-semibold">{workQueue?.alerts_new ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Acknowledged alerts</span>
              <span className="font-semibold">{workQueue?.alerts_acknowledged ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Open incidents</span>
              <span className="font-semibold">{workQueue?.incidents_open ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Investigating incidents</span>
              <span className="font-semibold">{workQueue?.incidents_investigating ?? 0}</span>
            </div>
            <div className="mt-3 rounded-md border border-red-500/30 bg-red-500/10 px-2 py-1.5 text-xs text-red-300">
              Overdue unresolved incidents: {workQueue?.incidents_overdue ?? 0}
            </div>
          </CardContent>
        </Card>
        <Card className="border-border/60 bg-card/40">
          <CardHeader>
            <CardTitle className="text-base">Top risks now</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(charts?.top_risks ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground">No active high-risk sources in this window.</p>
            ) : (
              (charts?.top_risks ?? []).slice(0, 5).map((risk) => (
                <div
                  key={risk.source_ip}
                  className="flex items-center justify-between rounded-md border border-border/50 px-2 py-1.5 text-xs"
                >
                  <span className="font-mono text-cyan-300">{risk.source_ip}</span>
                  <span className="text-muted-foreground">
                    HC events: <span className="font-semibold text-foreground">{risk.high_critical_events}</span>
                  </span>
                  <span className="text-muted-foreground">
                    Alerts: <span className="font-semibold text-foreground">{risk.alerts}</span>
                  </span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
        <Card className="border-border/60 bg-card/40">
          <CardHeader>
            <CardTitle className="text-base">Detection quality snapshot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Event → Alert conversion</span>
              <span className="font-semibold">{summary?.event_to_alert_conversion_pct ?? 0}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">MITRE coverage (techniques)</span>
              <span className="font-semibold">{summary?.mitre_coverage_count ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Auth anomaly alerts</span>
              <span className="font-semibold">{anomalySignals?.auth_anomaly_alerts ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Exfiltration alerts</span>
              <span className="font-semibold">{anomalySignals?.exfiltration_alerts ?? 0}</span>
            </div>
          </CardContent>
        </Card>
      </div>
      {summary?.security_overview && (
        <Card className="border-cyan-500/20 bg-gradient-to-br from-cyan-500/5 to-violet-500/5">
          <CardHeader>
            <CardTitle className="text-base">Security overview</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground leading-relaxed">{summary.security_overview}</p>
          </CardContent>
        </Card>
      )}
      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="text-base">UI/UX advisor agent</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {uiRecommendationsFiltered.length === 0 ? (
            <p className="text-sm text-muted-foreground">No advisor tips for the current posture.</p>
          ) : null}
          {uiRecommendationsFiltered.map((rec) => (
            <div
              key={rec.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border/50 px-3 py-2 text-sm"
            >
              <div>
                <p className="font-medium">{rec.title}</p>
                <p className="text-xs text-muted-foreground">{rec.rationale}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded-md border border-border/60 px-2 py-1 text-xs capitalize text-muted-foreground">
                  <CircleDot className="h-3 w-3 text-cyan-400" />
                  {rec.severity}
                </span>
                <Link href={rec.action_href} className={cn(buttonVariants({ size: "sm" }))}>
                  {rec.action_label}
                </Link>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
      {charts && <OverviewCharts data={charts} />}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-border/60 bg-card/40">
          <CardHeader>
            <CardTitle className="text-base">Recent incidents</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(recentInc ?? []).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="py-8 text-center">
                      <div className="flex flex-col items-center gap-2 text-muted-foreground">
                        <FileWarning className="h-7 w-7 opacity-40" />
                        <p className="text-xs font-medium">No incidents yet</p>
                        <Link
                          href="/attack-lab"
                          className="flex items-center gap-1 text-[11px] text-cyan-400 hover:underline"
                        >
                          <FlaskConical className="h-3 w-3" />
                          Run an attack scenario
                        </Link>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  (recentInc ?? []).map((r) => (
                    <TableRow key={r.id}>
                      <TableCell>
                        <Link href={`/incidents/${r.id}`} className="text-cyan-400 hover:underline">
                          {r.title}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <SeverityBadge severity={r.severity} />
                      </TableCell>
                      <TableCell className="capitalize">{r.status.replace("_", " ")}</TableCell>
                      <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                        {new Date(r.created_at).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
        <Card className="border-border/60 bg-card/40">
          <CardHeader>
            <CardTitle className="text-base">Recent alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Alert</TableHead>
                  <TableHead>Rule</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(recentAlerts ?? []).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="py-8 text-center">
                      <div className="flex flex-col items-center gap-2 text-muted-foreground">
                        <ShieldOff className="h-7 w-7 opacity-40" />
                        <p className="text-xs font-medium">No alerts detected</p>
                        <Link
                          href="/attack-lab"
                          className="flex items-center gap-1 text-[11px] text-cyan-400 hover:underline"
                        >
                          <FlaskConical className="h-3 w-3" />
                          Launch an attack to trigger alerts
                        </Link>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  (recentAlerts ?? []).map((a) => (
                    <TableRow key={a.id}>
                      <TableCell className="max-w-[180px] truncate">{a.title}</TableCell>
                      <TableCell className="text-muted-foreground">{a.rule_name}</TableCell>
                      <TableCell>
                        <SeverityBadge severity={a.severity} />
                      </TableCell>
                      <TableCell className="capitalize text-xs text-muted-foreground">{a.status}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-4 lg:grid-cols-4">
        <Card className="border-border/60 bg-card/40 lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Siren className="h-4 w-4 text-orange-400" />
              Exfiltration watch
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Exfil alerts</span>
              <span className="font-semibold">{anomalySignals?.exfiltration_alerts ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Outbound transfer events</span>
              <span className="font-semibold">{anomalySignals?.outbound_transfer_events ?? 0}</span>
            </div>
          </CardContent>
        </Card>
        <Card className="border-border/60 bg-card/40 lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ShieldCheck className="h-4 w-4 text-violet-400" />
              Identity anomalies
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Auth anomaly alerts</span>
              <span className="font-semibold">{anomalySignals?.auth_anomaly_alerts ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Privileged logins</span>
              <span className="font-semibold">{anomalySignals?.privileged_login_events ?? 0}</span>
            </div>
          </CardContent>
        </Card>
        <Card className="border-border/60 bg-card/40 lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Most active detection rules</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(charts?.top_rules_24h ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground">No rule activity in selected window.</p>
            ) : (
              (charts?.top_rules_24h ?? []).slice(0, 6).map((rule) => (
                <div key={rule.rule_name} className="flex items-center justify-between rounded-md border border-border/50 px-2 py-1.5 text-xs">
                  <span className="font-mono text-cyan-300">{rule.rule_name}</span>
                  <span className="text-muted-foreground">
                    Hits: <span className="font-semibold text-foreground">{rule.count}</span>
                  </span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
