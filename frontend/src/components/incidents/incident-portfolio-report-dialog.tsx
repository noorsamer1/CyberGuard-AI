"use client";

import Link from "next/link";
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

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { IncidentPortfolioReport } from "@/lib/api/types";
import { downloadIncidentPortfolioHtml } from "@/lib/incident-portfolio-html";

import styles from "./incident-portfolio-report-dialog.module.css";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  report: IncidentPortfolioReport | null;
  isLoading: boolean;
};

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border/60 bg-muted/20 p-3">
      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">{title}</p>
      <div className="h-[220px] w-full min-w-0">{children}</div>
    </div>
  );
}

export function IncidentPortfolioReportDialog({ open, onOpenChange, report, isLoading }: Props) {
  function handleDownload() {
    if (report) downloadIncidentPortfolioHtml(report);
  }

  const spike = Boolean(report?.stats?.spike_last_period);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] max-w-4xl gap-0 p-0 sm:max-w-4xl" showCloseButton>
        <div
          className={cn(
            "flex flex-wrap items-center justify-end gap-2 border-b border-border/60 px-4 py-3",
            styles.toolbar,
          )}
        >
          <Button type="button" variant="outline" size="sm" disabled={!report || isLoading} onClick={handleDownload}>
            Download HTML
          </Button>
        </div>
        <DialogHeader className="border-b border-border/60 px-4 py-4">
          <DialogTitle>AI incident portfolio report</DialogTitle>
          <DialogDescription>
            Charts use your database aggregates; AI text is advisory and must not change stored incidents.
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[calc(92vh-10rem)]">
          <div className="space-y-6 px-4 py-4">
            {isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-48 w-full" />
                <Skeleton className="h-48 w-full" />
              </div>
            ) : !report ? (
              <p className="text-sm text-muted-foreground">No report data.</p>
            ) : (
              <>
                <div className="rounded-md border border-border/50 bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
                  <p>
                    Generated {new Date(report.generated_at).toLocaleString()} · Filters: severity=
                    {report.filters.severity ?? "all"}, status={report.filters.status ?? "all"}, search=
                    {report.filters.q ? `"${report.filters.q}"` : "—"}
                  </p>
                  {report.truncation_note && (
                    <p className="mt-1 text-amber-600/90">{report.truncation_note}</p>
                  )}
                  {spike && (
                    <p className="mt-1 font-medium text-cyan-600">
                      Pattern: last week bucket is elevated vs prior average (see weekly chart).
                    </p>
                  )}
                </div>

                {report.ai_error && (
                  <div className="rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-100">
                    {report.ai_error}
                  </div>
                )}

                <div className="grid gap-4 md:grid-cols-2">
                  <ChartCard title="Severity (all matching)">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={report.charts.severity_bar} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
                        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                        <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={32} />
                        <Tooltip contentStyle={{ fontSize: 12 }} />
                        <Bar dataKey="count" fill="var(--color-cyan-500, #06b6d4)" radius={[4, 4, 0, 0]} name="Count" />
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartCard>
                  <ChartCard title="Status (all matching)">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={report.charts.status_bar} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
                        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                        <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={32} />
                        <Tooltip contentStyle={{ fontSize: 12 }} />
                        <Bar dataKey="count" fill="var(--color-violet-500, #8b5cf6)" radius={[4, 4, 0, 0]} name="Count" />
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartCard>
                </div>

                <ChartCard title="New incidents by week (UTC)">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={report.charts.weekly_line} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
                      <XAxis
                        dataKey="week_start"
                        tick={{ fontSize: 10 }}
                        tickFormatter={(v) => (typeof v === "string" ? v.slice(0, 10) : String(v))}
                      />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={32} />
                      <Tooltip labelFormatter={(v) => String(v).slice(0, 10)} contentStyle={{ fontSize: 12 }} />
                      <Line type="monotone" dataKey="count" stroke="#22d3ee" strokeWidth={2} dot name="Created" />
                    </LineChart>
                  </ResponsiveContainer>
                </ChartCard>

                <div className="grid gap-4 md:grid-cols-2">
                  <ChartCard title="Top rules (linked alerts, sample)">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        layout="vertical"
                        data={report.charts.rules_bar}
                        margin={{ top: 8, right: 8, left: 4, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
                        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                        <YAxis type="category" dataKey="rule_name" width={100} tick={{ fontSize: 10 }} />
                        <Tooltip contentStyle={{ fontSize: 12 }} />
                        <Bar dataKey="count" fill="#a78bfa" radius={[0, 4, 4, 0]} name="Count" />
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartCard>
                  <ChartCard title="MITRE techniques (weighted)">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        layout="vertical"
                        data={report.charts.mitre_bar}
                        margin={{ top: 8, right: 8, left: 4, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
                        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                        <YAxis type="category" dataKey="technique_id" width={56} tick={{ fontSize: 10 }} />
                        <Tooltip contentStyle={{ fontSize: 12 }} />
                        <Bar dataKey="count" fill="#34d399" radius={[0, 4, 4, 0]} name="Weight" />
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartCard>
                </div>

                <div>
                  <h3 className="mb-2 text-sm font-medium text-foreground">Oldest open backlog</h3>
                  <ul className="space-y-1 text-sm">
                    {((report.stats.oldest_open as Array<{ id: number; title: string; days_open: number }>) ?? []).map(
                      (o) => (
                        <li key={o.id} className="flex flex-wrap gap-2 text-muted-foreground">
                          <Link href={`/incidents/${o.id}`} className="font-mono text-cyan-400 hover:underline">
                            #{o.id}
                          </Link>
                          <span className="text-foreground/90">{o.title}</span>
                          <span className="text-xs">({o.days_open}d open)</span>
                        </li>
                      ),
                    )}
                  </ul>
                </div>

                {report.ai && (
                  <div className="space-y-4 rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-4">
                    <h3 className="text-sm font-semibold text-cyan-200">AI narrative</h3>
                    <p className="text-sm leading-relaxed text-foreground/90">{report.ai.executive_summary}</p>
                    {report.ai.key_findings.length > 0 && (
                      <div>
                        <p className="mb-1 text-xs font-medium uppercase text-muted-foreground">Key findings</p>
                        <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                          {report.ai.key_findings.map((x, i) => (
                            <li key={i}>{x}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {report.ai.risks.length > 0 && (
                      <div>
                        <p className="mb-1 text-xs font-medium uppercase text-muted-foreground">Risks</p>
                        <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                          {report.ai.risks.map((x, i) => (
                            <li key={i}>{x}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {report.ai.recommendations.length > 0 && (
                      <div>
                        <p className="mb-1 text-xs font-medium uppercase text-muted-foreground">Recommendations</p>
                        <ol className="list-inside list-decimal space-y-1 text-sm text-muted-foreground">
                          {report.ai.recommendations.map((x, i) => (
                            <li key={i}>{x}</li>
                          ))}
                        </ol>
                      </div>
                    )}
                    {report.ai.themes.length > 0 && (
                      <div>
                        <p className="mb-1 text-xs font-medium uppercase text-muted-foreground">Themes</p>
                        <div className="flex flex-wrap gap-2">
                          {report.ai.themes.map((t, i) => (
                            <span
                              key={i}
                              className="rounded-full border border-border/60 bg-background/80 px-2 py-0.5 text-xs"
                            >
                              {t}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <p className="text-[11px] text-muted-foreground">
                  Downloaded HTML mirrors this view for sharing or archiving.
                </p>
              </>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
