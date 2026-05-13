"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { FileText, FolderOpen } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { apiFetch } from "@/lib/api/client";
import type { Paginated, Report } from "@/lib/api/types";

export default function ReportsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: () => apiFetch<Paginated<Report>>("/reports?page=1&page_size=50"),
  });

  async function download(id: number) {
    try {
      const token = localStorage.getItem("cg_access_token");
      const { API_BASE } = await import("@/lib/constants");
      const res = await fetch(`${API_BASE}/api/v1/reports/${id}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `cyberguard-report-${id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Download started");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Download failed");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Reports</h1>
        <p className="text-sm text-muted-foreground">PDF exports generated from incidents.</p>
      </div>
      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="text-base">Library</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Incident</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Download</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-36" /></TableCell>
                    <TableCell className="text-right"><Skeleton className="ml-auto h-7 w-14" /></TableCell>
                  </TableRow>
                ))
              ) : (data?.items ?? []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="py-12 text-center">
                    <div className="flex flex-col items-center gap-3 text-muted-foreground">
                      <FolderOpen className="h-9 w-9 opacity-50" />
                      <div>
                        <p className="font-medium">No reports generated yet</p>
                        <p className="mt-0.5 text-xs">
                          Open an incident and click &ldquo;Generate PDF&rdquo; to create your first report.
                        </p>
                      </div>
                      <Link
                        href="/incidents"
                        className={cn(buttonVariants({ variant: "outline", size: "sm" }), "mt-1")}
                      >
                        Go to Incidents
                      </Link>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                (data?.items ?? []).map((r, i) => (
                  <motion.tr
                    key={r.id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="border-b transition-colors hover:bg-muted/50"
                  >
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      #{r.id}
                    </TableCell>
                    <TableCell>
                      <Link
                        href={`/incidents/${r.incident_id}`}
                        className="flex items-center gap-1.5 text-cyan-400 hover:underline"
                      >
                        <FileText className="h-3.5 w-3.5 shrink-0" />
                        Incident #{r.incident_id}
                      </Link>
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                      {new Date(r.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button size="sm" variant="outline" onClick={() => download(r.id)}>
                        PDF
                      </Button>
                    </TableCell>
                  </motion.tr>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
