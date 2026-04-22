"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { FileWarning } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { SeverityBadge } from "@/components/common/severity-badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
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
import { apiFetch } from "@/lib/api/client";
import type { Incident, Paginated } from "@/lib/api/types";

export default function IncidentsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({
    queryKey: ["incidents", page],
    queryFn: () =>
      apiFetch<Paginated<Incident>>(`/incidents?page=${page}&page_size=20`),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Incidents</h1>
          <p className="text-sm text-muted-foreground">Investigations linked to events and AI notes.</p>
        </div>
        <Link href="/dashboard" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
          Back to overview
        </Link>
      </div>
      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="text-base">Case queue</CardTitle>
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
                    <TableCell><Skeleton className="h-4 w-52" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-16 rounded-full" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                  </TableRow>
                ))
              ) : (data?.items ?? []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="py-12 text-center">
                    <div className="flex flex-col items-center gap-2 text-muted-foreground">
                      <FileWarning className="h-8 w-8" />
                      <p className="font-medium">No incidents yet</p>
                      <p className="text-xs">Incidents are created automatically when alerts are correlated.</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                (data?.items ?? []).map((inc, i) => (
                  <motion.tr
                    key={inc.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"
                  >
                    <TableCell>
                      <Link href={`/incidents/${inc.id}`} className="font-medium text-cyan-400 hover:underline">
                        {inc.title}
                      </Link>
                      <p className="text-xs text-muted-foreground line-clamp-1">{inc.summary}</p>
                    </TableCell>
                    <TableCell>
                      <SeverityBadge severity={inc.severity} />
                    </TableCell>
                    <TableCell className="capitalize">{inc.status.replace("_", " ")}</TableCell>
                    <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                      {new Date(inc.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>{inc.events?.length ?? 0}</TableCell>
                  </motion.tr>
                ))
              )}
            </TableBody>
          </Table>
          <div className="mt-4 flex justify-between text-sm text-muted-foreground">
            <span>Total {data?.total ?? 0}</span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
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
