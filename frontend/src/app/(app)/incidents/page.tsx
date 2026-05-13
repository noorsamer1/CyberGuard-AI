"use client";

import { useQuery } from "@tanstack/react-query";
import { FileBarChart, FileWarning, Search } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { IncidentPortfolioReportDialog } from "@/components/incidents/incident-portfolio-report-dialog";
import { SeverityBadge } from "@/components/common/severity-badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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
import type { Incident, IncidentPortfolioReport, Paginated } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 20;

export default function IncidentsPage() {
  const [page, setPage] = useState(1);
  const [severity, setSeverity] = useState<string>("all");
  const [status, setStatus] = useState<string>("all");
  const [q, setQ] = useState("");
  const [reportOpen, setReportOpen] = useState(false);
  const [report, setReport] = useState<IncidentPortfolioReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["incidents", page, severity, status, q],
    queryFn: () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(PAGE_SIZE),
      });
      if (severity !== "all") params.set("severity", severity);
      if (status !== "all") params.set("status", status);
      if (q.trim()) params.set("q", q.trim());
      return apiFetch<Paginated<Incident>>(`/incidents?${params}`);
    },
  });

  async function generatePortfolioReport() {
    setReportOpen(true);
    setReportLoading(true);
    setReport(null);
    try {
      const body: Record<string, unknown> = { max_items: 150 };
      if (severity !== "all") body.severity = severity;
      if (status !== "all") body.status = status;
      if (q.trim()) body.q = q.trim();
      const result = await apiFetch<IncidentPortfolioReport>("/incidents/portfolio-report", {
        method: "POST",
        json: body,
      });
      setReport(result);
      if (result.ai_error) {
        toast.message("Report ready", { description: result.ai_error });
      } else {
        toast.success("Portfolio report ready");
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Report failed");
      setReportOpen(false);
    } finally {
      setReportLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <IncidentPortfolioReportDialog
        open={reportOpen}
        onOpenChange={setReportOpen}
        report={report}
        isLoading={reportLoading}
      />
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Incidents</h1>
          <p className="text-sm text-muted-foreground">Investigations linked to events and AI notes.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="default" size="sm" className="gap-1.5" onClick={() => void generatePortfolioReport()}>
            <FileBarChart className="h-4 w-4" />
            AI portfolio report
          </Button>
          <Link href="/dashboard" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
            Back to overview
          </Link>
        </div>
      </div>
      <Card className="border-border/60 bg-card/40">
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="text-base">Case queue</CardTitle>
          <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:flex-wrap sm:items-center">
            <div className="relative min-w-[200px] flex-1 sm:max-w-xs">
              <Search className="absolute top-1/2 left-2.5 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Search title or summary…"
                value={q}
                onChange={(e) => {
                  setQ(e.target.value);
                  setPage(1);
                }}
              />
            </div>
            <Select
              value={severity}
              onValueChange={(v) => {
                if (v) {
                  setSeverity(v);
                  setPage(1);
                }
              }}
            >
              <SelectTrigger className="w-full sm:w-[140px]">
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
              <SelectTrigger className="w-full sm:w-[160px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="investigating">Investigating</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="false_positive">False positive</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Events</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <Skeleton className="h-4 w-52" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-5 w-16 rounded-full" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-24" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-32" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-8" />
                    </TableCell>
                  </TableRow>
                ))
              ) : (data?.items ?? []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="py-12 text-center">
                    <div className="flex flex-col items-center gap-2 text-muted-foreground">
                      <FileWarning className="h-8 w-8" />
                      <p className="font-medium">No incidents yet</p>
                      <p className="text-xs">Adjust filters or ingest events to populate this queue.</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                (data?.items ?? []).map((inc) => (
                  <TableRow key={inc.id}>
                    <TableCell>
                      <Link href={`/incidents/${inc.id}`} className="font-medium text-cyan-400 hover:underline">
                        {inc.title}
                      </Link>
                      <p className="line-clamp-1 text-xs text-muted-foreground">{inc.summary}</p>
                    </TableCell>
                    <TableCell>
                      <SeverityBadge severity={inc.severity} />
                    </TableCell>
                    <TableCell className="capitalize">{inc.status.replace("_", " ")}</TableCell>
                    <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                      {new Date(inc.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>{inc.events?.length ?? 0}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
          <div className="mt-4 flex flex-col gap-2 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
            <span>Total {data?.total ?? 0}</span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Prev
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!data || page * (data.page_size ?? PAGE_SIZE) >= data.total}
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
