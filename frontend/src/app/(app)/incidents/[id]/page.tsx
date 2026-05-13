"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Clock, ChevronRight, Shield, Crosshair } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { SeverityBadge } from "@/components/common/severity-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api/client";
import type { AIClassification, Incident, IncidentBriefing } from "@/lib/api/types";

function AIDetectionSummary({ assessment }: { assessment: AIClassification }) {
  const confidence = Math.round((assessment.confidence ?? 0) * 100);
  return (
    <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-3">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="border-cyan-500/30 bg-cyan-500/10 text-cyan-300">
          <Sparkles className="mr-1 h-3 w-3" />
          {assessment.attack_type.replaceAll("_", " ")}
        </Badge>
        <span className="text-xs text-muted-foreground">{confidence}% confidence</span>
        <span className="text-xs text-muted-foreground">
          Suggested severity: <span className="capitalize text-foreground/80">{assessment.suggested_severity}</span>
        </span>
      </div>
      <p className="text-sm text-muted-foreground">{assessment.why_classified}</p>
      {assessment.evidence.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {assessment.evidence.slice(0, 4).map((item) => (
            <span
              key={item}
              className="rounded border border-border/60 bg-card/40 px-1.5 py-0.5 text-[11px] text-muted-foreground"
            >
              {item}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function IncidentDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const router = useRouter();
  const qc = useQueryClient();

  const { data: inc, isLoading } = useQuery({
    queryKey: ["incident", id],
    queryFn: () => apiFetch<Incident>(`/incidents/${id}`),
    enabled: Number.isFinite(id),
  });
  const [briefingMode, setBriefingMode] = useState<"executive" | "technical">("executive");
  const briefingQuery = useQuery({
    queryKey: ["incident-briefing", id, briefingMode],
    queryFn: () =>
      apiFetch<IncidentBriefing>(`/incidents/${id}/briefing?mode=${briefingMode}`),
    enabled: Number.isFinite(id),
  });

  const analyze = useMutation({
    mutationFn: () =>
      apiFetch<Incident>(`/incidents/${id}/analyze?async_task=false`, { method: "POST" }),
    onSuccess: () => {
      toast.success("AI analysis complete");
      qc.invalidateQueries({ queryKey: ["incident", id] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const report = useMutation({
    mutationFn: (emailCopy: boolean) =>
      apiFetch<{ message: string }>(
        `/incidents/${id}/generate-report${emailCopy ? "?email_copy=true" : ""}`,
        { method: "POST" },
      ),
    onSuccess: (r) => {
      toast.success(r.message);
      qc.invalidateQueries({ queryKey: ["reports"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  if (!Number.isFinite(id)) {
    return <p className="text-muted-foreground">Invalid incident</p>;
  }

  if (isLoading || !inc) {
    return (
      <div className="mx-auto max-w-5xl space-y-6">
        {/* Header skeleton */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-7 w-80" />
            <div className="flex gap-2">
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-5 w-20 rounded-md" />
            </div>
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-9 w-32" />
            <Skeleton className="h-9 w-28" />
          </div>
        </div>
        {/* Summary card skeleton */}
        <Card className="border-border/60 bg-card/40">
          <CardHeader><Skeleton className="h-4 w-20" /></CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-4/6" />
          </CardContent>
        </Card>
        {/* Events card skeleton */}
        <Card className="border-border/60 bg-card/40">
          <CardHeader><Skeleton className="h-4 w-28" /></CardHeader>
          <CardContent className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex gap-4">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 flex-1" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  const aiAssessments = (inc.events ?? [])
    .map((event) => event.ai_assessment)
    .filter((item): item is AIClassification => Boolean(item));

  return (
    <div className="relative mx-auto max-w-5xl space-y-6">
      <AnimatePresence>
        {analyze.isPending && (
          <motion.div
            role="status"
            aria-live="polite"
            aria-busy="true"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 z-20 flex items-start justify-center rounded-lg bg-background/70 pt-24 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.96, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.98, opacity: 0 }}
              className="flex flex-col items-center gap-3 rounded-xl border border-cyan-500/30 bg-card/95 px-8 py-6 shadow-lg"
            >
              <motion.div
                animate={{ rotate: [0, 8, -8, 0] }}
                transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
              >
                <Sparkles className="h-10 w-10 text-cyan-400" />
              </motion.div>
              <p className="text-sm font-medium text-foreground">Running AI analysis…</p>
              <motion.div
                className="h-1 w-40 overflow-hidden rounded-full bg-muted"
                aria-hidden
              >
                <motion.div
                  className="h-full bg-gradient-to-r from-cyan-500 to-violet-500"
                  initial={{ x: "-100%" }}
                  animate={{ x: "100%" }}
                  transition={{ duration: 1.1, repeat: Infinity, ease: "easeInOut" }}
                  style={{ width: "45%" }}
                />
              </motion.div>
              <p className="max-w-xs text-center text-xs text-muted-foreground">
                Generating summary and remediation from incident context.
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Button variant="ghost" size="sm" className="mb-2 -ml-2" onClick={() => router.push("/incidents")}>
            ← Incidents
          </Button>
          <h1 className="text-2xl font-semibold">{inc.title}</h1>
          <div className="mt-2 flex flex-wrap gap-2">
            <SeverityBadge severity={inc.severity} />
            <span className="rounded-md border border-border/60 px-2 py-0.5 text-xs capitalize">
              {inc.status.replace("_", " ")}
            </span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => analyze.mutate()} disabled={analyze.isPending}>
            {analyze.isPending ? (
              <span className="inline-flex items-center gap-2">
                <motion.span
                  className="inline-block h-3.5 w-3.5 rounded-full border-2 border-cyan-400 border-t-transparent"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 0.7, repeat: Infinity, ease: "linear" }}
                />
                Analyzing…
              </span>
            ) : (
              "Run AI analysis"
            )}
          </Button>
          <Button onClick={() => report.mutate(false)} disabled={report.isPending}>
            Generate PDF
          </Button>
          <Button variant="secondary" onClick={() => report.mutate(true)} disabled={report.isPending}>
            Generate and email PDF
          </Button>
        </div>
      </div>
      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="text-base">Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <p className="text-muted-foreground">{inc.summary}</p>
          {inc.ai_summary && (
            <>
              <Separator />
              <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-4">
                <div className="mb-2 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-cyan-400" />
                  <h3 className="text-sm font-medium text-cyan-300">AI Analysis</h3>
                </div>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">{inc.ai_summary}</p>
              </div>
            </>
          )}
          {inc.remediation && (
            <>
              <Separator />
              <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4">
                <div className="mb-2 flex items-center gap-2">
                  <Shield className="h-4 w-4 text-emerald-400" />
                  <h3 className="text-sm font-medium text-emerald-300">Remediation</h3>
                </div>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">{inc.remediation}</p>
              </div>
            </>
          )}
          {inc.analyst_notes && (
            <>
              <Separator />
              <div>
                <h3 className="mb-1 font-medium text-foreground">Analyst notes</h3>
                <p className="text-muted-foreground whitespace-pre-wrap">{inc.analyst_notes}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>
      {aiAssessments.length > 0 && (
        <Card className="border-border/60 bg-card/40">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-cyan-400" />
              <CardTitle className="text-base">AI Detection Copilot</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Event-level AI classification is separate from manual incident analysis. Rule severity remains the official SOC severity.
            </p>
            <div className="grid gap-3 md:grid-cols-2">
              {aiAssessments.slice(0, 6).map((assessment) => (
                <AIDetectionSummary key={assessment.id} assessment={assessment} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle className="text-base">Threat briefing agent</CardTitle>
            <div className="flex items-center gap-1 rounded-md border border-border/60 p-1">
              <Button
                size="sm"
                variant={briefingMode === "executive" ? "default" : "ghost"}
                className="h-7 px-2 text-xs"
                onClick={() => setBriefingMode("executive")}
              >
                Executive
              </Button>
              <Button
                size="sm"
                variant={briefingMode === "technical" ? "default" : "ghost"}
                className="h-7 px-2 text-xs"
                onClick={() => setBriefingMode("technical")}
              >
                Technical
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {briefingQuery.isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
            </div>
          ) : !briefingQuery.data ? (
            <p className="text-muted-foreground">Briefing is unavailable right now.</p>
          ) : (
            <>
              <p className="text-muted-foreground">{briefingQuery.data.executive_summary}</p>
              <div className="rounded-md border border-cyan-500/20 bg-cyan-500/5 p-3">
                <p className="text-xs uppercase tracking-wide text-cyan-300">Business impact</p>
                <p className="mt-1 text-sm text-muted-foreground">{briefingQuery.data.business_impact}</p>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="rounded-md border border-border/50 p-3">
                  <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">
                    Recommended actions
                  </p>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    {briefingQuery.data.recommended_actions.map((item) => (
                      <li key={item}>- {item}</li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-md border border-border/50 p-3">
                  <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">
                    Learning benchmark
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Avg score: {briefingQuery.data.learning_benchmark.average_score ?? "—"} | Latest:{" "}
                    {briefingQuery.data.learning_benchmark.latest_score ?? "—"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Completed sessions: {briefingQuery.data.learning_benchmark.sessions_completed}
                  </p>
                  <p className="text-sm text-cyan-300">
                    Trend: {briefingQuery.data.learning_benchmark.trend}
                  </p>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Attack Timeline */}
      {(inc.events ?? []).length > 0 && (
        <Card className="border-border/60 bg-card/40">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-cyan-400" />
              <CardTitle className="text-base">Attack Timeline</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="relative">
              {/* vertical spine */}
              <div className="absolute left-[7px] top-0 h-full w-px bg-border/60" />
              <div className="space-y-3 pl-7">
                {[...(inc.events ?? [])]
                  .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
                  .map((e, i) => {
                    const severityDot: Record<string, string> = {
                      critical: "bg-red-500",
                      high: "bg-orange-500",
                      medium: "bg-amber-500",
                      low: "bg-emerald-500",
                    };
                    const dot = severityDot[e.severity ?? "low"] ?? "bg-muted";
                    return (
                      <motion.div
                        key={e.id}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.03 }}
                        className="relative"
                      >
                        {/* dot on spine */}
                        <span
                          className={`absolute -left-[24px] top-[5px] h-2.5 w-2.5 rounded-full ring-2 ring-background ${dot}`}
                        />
                        <div className="rounded-lg border border-border/40 bg-muted/20 px-3 py-2">
                          <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                            <span className="font-mono text-white/60">
                              {new Date(e.timestamp).toLocaleTimeString()}
                            </span>
                            <span className="rounded bg-muted/50 px-1.5 py-0.5 font-mono">
                              {e.event_type}
                            </span>
                            {e.source_ip && (
                              <span className="font-mono">{e.source_ip}</span>
                            )}
                            {e.port && (
                              <span className="font-mono text-cyan-400/70">:{e.port}</span>
                            )}
                            <span
                              className={`rounded px-1.5 py-0.5 text-[10px] font-medium capitalize ${dot.replace("bg-", "text-").replace("-500", "-400")}`}
                            >
                              {e.severity}
                            </span>
                          </div>
                          <p className="mt-0.5 text-xs text-foreground/80">
                            {e.message ?? e.raw_log ?? "—"}
                          </p>
                          {e.ai_assessment && (
                            <div className="mt-2">
                              <AIDetectionSummary assessment={e.ai_assessment} />
                            </div>
                          )}
                        </div>
                      </motion.div>
                    );
                  })}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* MITRE ATT&CK Section */}
      {(inc.mitre_techniques ?? []).length > 0 && (
        <Card className="border-border/60 bg-card/40">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Crosshair className="h-4 w-4 text-violet-400" />
              <CardTitle className="text-base">MITRE ATT&CK Coverage</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {(inc.mitre_techniques ?? []).map((tag) => (
                <a
                  key={tag.technique_id}
                  href={`https://attack.mitre.org/techniques/${tag.technique_id.replace(".", "/")}/`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 rounded border border-violet-500/30 bg-violet-500/10 px-2.5 py-1.5 text-xs text-violet-300 transition-opacity hover:opacity-80"
                >
                  <span className="font-mono font-semibold">{tag.technique_id}</span>
                  <ChevronRight className="h-3 w-3 opacity-60" />
                  <span>{tag.technique}</span>
                  <span className="opacity-60">· {tag.tactic}</span>
                </a>
              ))}
            </div>
            {(inc.threat_profiles ?? []).length > 0 && (
              <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-amber-300">
                  Threat Intelligence Profile
                </p>
                <div className="space-y-2 text-xs text-muted-foreground">
                  {(inc.threat_profiles ?? []).map((profile) => (
                    <div key={profile.actor} className="rounded border border-border/40 bg-card/30 p-2">
                      <p className="font-medium text-foreground">{profile.actor}</p>
                      <p>Kill chain phase: {profile.kill_chain_phase}</p>
                      <p className="capitalize">Confidence: {profile.confidence}</p>
                      {profile.cve_references.length > 0 && (
                        <p className="mt-1 font-mono text-[11px] text-amber-300/90">
                          {profile.cve_references.join(", ")}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              Generated from detection rule intelligence. Click any technique to open MITRE ATT&CK reference.
            </p>
          </CardContent>
        </Card>
      )}

      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="text-base">Related events</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Port</TableHead>
                <TableHead>Message</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(inc.events ?? []).map((e) => (
                <TableRow key={e.id}>
                  <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                    {new Date(e.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell>{e.event_type}</TableCell>
                  <TableCell>{e.source_ip ?? "—"}</TableCell>
                  <TableCell className="font-mono text-xs">{e.port ?? "—"}</TableCell>
                  <TableCell className="max-w-md truncate">{e.message ?? e.raw_log ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
