"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useState } from "react";
import { ShieldOff, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { AlertAIInsightDialog } from "@/components/alerts/alert-ai-insight-dialog";
import { SeverityBadge } from "@/components/common/severity-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import type { AIClassification, Alert, AlertStatus, Paginated } from "@/lib/api/types";

function AIAssessment({ assessment }: { assessment: AIClassification | null }) {
  if (!assessment) {
    return <span className="text-xs text-muted-foreground">Pending</span>;
  }
  const confidence = Math.round((assessment.confidence ?? 0) * 100);
  return (
    <div className="max-w-[220px] space-y-1">
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge variant="outline" className="border-cyan-500/30 bg-cyan-500/10 text-[10px] text-cyan-300">
          <Sparkles className="mr-1 h-3 w-3" />
          {assessment.attack_type.replaceAll("_", " ")}
        </Badge>
        <span className="text-[11px] text-muted-foreground">{confidence}%</span>
      </div>
      <p className="line-clamp-2 text-xs text-muted-foreground">{assessment.why_classified}</p>
      <p className="text-[11px] text-muted-foreground">
        Suggested: <span className="capitalize text-foreground/80">{assessment.suggested_severity}</span>
      </p>
    </div>
  );
}

export default function AlertsPage() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [severity, setSeverity] = useState<string>("all");
  const [status, setStatus] = useState<string>("all");
  const [insightAlert, setInsightAlert] = useState<Alert | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["alerts", page, severity, status],
    queryFn: () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "20",
      });
      if (severity !== "all") params.set("severity", severity);
      if (status !== "all") params.set("status", status);
      return apiFetch<Paginated<Alert>>(`/alerts?${params}`);
    },
  });

  async function updateStatus(id: number, s: AlertStatus) {
    try {
      await apiFetch(`/alerts/${id}/status`, { method: "PATCH", json: { status: s } });
      toast.success("Alert updated");
      qc.invalidateQueries({ queryKey: ["alerts"] });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Update failed");
    }
  }

  return (
    <div className="space-y-6">
      <AlertAIInsightDialog
        alert={insightAlert}
        open={insightAlert !== null}
        onOpenChange={(o) => {
          if (!o) setInsightAlert(null);
        }}
        onClassificationStored={() => {
          void qc.invalidateQueries({ queryKey: ["alerts"] });
        }}
      />
      <div>
        <h1 className="text-2xl font-semibold">Alert center</h1>
        <p className="text-sm text-muted-foreground">Triage, acknowledge, and resolve detections.</p>
      </div>
      <Card className="border-border/60 bg-card/40">
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="text-base">All alerts</CardTitle>
          <div className="flex flex-wrap gap-2">
            <Select
              value={severity}
              onValueChange={(v) => {
                if (v) {
                  setSeverity(v);
                  setPage(1);
                }
              }}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All severities</SelectItem>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={status}
              onValueChange={(v) => {
                if (v) {
                  setStatus(v);
                  setPage(1);
                }
              }}
            >
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="new">New</SelectItem>
                <SelectItem value="acknowledged">Acknowledged</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Rule</TableHead>
                <TableHead className="hidden xl:table-cell">MITRE</TableHead>
                <TableHead className="hidden 2xl:table-cell">AI assessment</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Triggered</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-4 w-48" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-28" /></TableCell>
                    <TableCell className="hidden xl:table-cell"><Skeleton className="h-4 w-20" /></TableCell>
                    <TableCell className="hidden 2xl:table-cell"><Skeleton className="h-10 w-44" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-16 rounded-full" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    <TableCell className="text-right"><Skeleton className="ml-auto h-7 w-24" /></TableCell>
                  </TableRow>
                ))
              ) : (data?.items ?? []).length === 0 ? (
                <TableRow>
                    <TableCell colSpan={8} className="py-12 text-center">
                    <div className="flex flex-col items-center gap-2 text-muted-foreground">
                      <ShieldOff className="h-8 w-8" />
                      <p className="font-medium">No alerts detected</p>
                      <p className="text-xs">Adjust your filters or ingest events to see alerts here.</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                (data?.items ?? []).map((a, i) => (
                  <motion.tr
                    key={a.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                  >
                    <TableCell>
                      <div className="max-w-xs">
                        <p className="font-medium">{a.title}</p>
                        {a.description && (
                          <p className="text-xs text-muted-foreground line-clamp-2">{a.description}</p>
                        )}
                        <div className="mt-2 2xl:hidden">
                          <AIAssessment assessment={a.ai_assessment} />
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{a.rule_name}</TableCell>
                    <TableCell className="hidden xl:table-cell">
                      <div className="flex flex-wrap gap-1">
                        {(a.mitre_techniques ?? []).slice(0, 2).map((t) => (
                          <span
                            key={t.technique_id}
                            className="rounded border border-violet-500/30 bg-violet-500/10 px-1.5 py-0.5 font-mono text-[10px] text-violet-300"
                            title={`${t.tactic} · ${t.technique}`}
                          >
                            {t.technique_id}
                          </span>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="hidden 2xl:table-cell">
                      <AIAssessment assessment={a.ai_assessment} />
                    </TableCell>
                    <TableCell>
                      <SeverityBadge severity={a.severity} />
                    </TableCell>
                    <TableCell className="capitalize">{a.status}</TableCell>
                    <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                      {new Date(a.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex flex-wrap justify-end gap-1">
                        <Button
                          size="sm"
                          variant="outline"
                          className="gap-1"
                          title={
                            a.event_id
                              ? "AI suggested severity, confidence, and rationale"
                              : "No linked event for AI context"
                          }
                          disabled={!a.event_id}
                          onClick={() => setInsightAlert(a)}
                        >
                          <Sparkles className="h-3.5 w-3.5" />
                          Insight
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => updateStatus(a.id, "acknowledged")}
                          disabled={a.status !== "new"}
                        >
                          Ack
                        </Button>
                        <Button size="sm" onClick={() => updateStatus(a.id, "resolved")}>
                          Resolve
                        </Button>
                      </div>
                    </TableCell>
                  </motion.tr>
                ))
              )}
            </TableBody>
          </Table>
          <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Page {data?.page ?? page} — {data?.total ?? 0} total
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Prev
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={data && data.items.length < 20}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
