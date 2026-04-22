"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api/client";
import type { ReportSchedule, Severity, User } from "@/lib/api/types";

const WEEKDAY_OPTIONS: { value: string; label: string }[] = [
  { value: "0", label: "Mon" },
  { value: "1", label: "Tue" },
  { value: "2", label: "Wed" },
  { value: "3", label: "Thu" },
  { value: "4", label: "Fri" },
  { value: "5", label: "Sat" },
  { value: "6", label: "Sun" },
];

function hhmmSchedule(s: string | null | undefined): string {
  if (!s || s.length < 4) return "";
  return s.slice(0, 5);
}

interface SettingsOut {
  notification_prefs: { email_alerts: boolean; push_alerts: boolean };
  demo_mode_hint: string;
}

function severityScheduleLabel(s: Severity): string {
  const m: Record<Severity, string> = {
    low: "All severities",
    medium: "Medium and above",
    high: "High and critical",
    critical: "Critical only",
  };
  return m[s];
}

function frequencyScheduleLabel(f: ReportSchedule["frequency"]): string {
  const m: Record<ReportSchedule["frequency"], string> = {
    hourly: "Hourly",
    twice_daily: "Every 12 hours",
    daily: "Daily",
    weekly: "Weekly",
  };
  return m[f];
}

export default function SettingsPage() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["settings"],
    queryFn: () => apiFetch<SettingsOut>("/settings"),
  });

  const { data: me } = useQuery({
    queryKey: ["me-profile"],
    queryFn: () => apiFetch<User>("/auth/me"),
  });

  const { data: schedules = [] } = useQuery({
    queryKey: ["report-schedules"],
    queryFn: () => apiFetch<ReportSchedule[]>("/report-schedules"),
  });

  const patch = useMutation({
    mutationFn: (prefs: SettingsOut["notification_prefs"]) =>
      apiFetch<SettingsOut>("/settings/notifications", { method: "PATCH", json: prefs }),
    onSuccess: (updated) => {
      qc.setQueryData(["settings"], updated);
      toast.success("Saved");
    },
  });

  const createSchedule = useMutation({
    mutationFn: (body: {
      min_severity: Severity;
      frequency: ReportSchedule["frequency"];
      recipient_email: string;
      enabled: boolean;
      preferred_time_utc: string | null;
      weekly_day_utc: number | null;
    }) => apiFetch<ReportSchedule>("/report-schedules", { method: "POST", json: body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["report-schedules"] });
      toast.success("Schedule created");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const patchSchedule = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: number;
      body: Partial<
        Pick<
          ReportSchedule,
          "enabled" | "min_severity" | "frequency" | "recipient_email" | "preferred_time_utc" | "weekly_day_utc"
        >
      >;
    }) => apiFetch<ReportSchedule>(`/report-schedules/${id}`, { method: "PATCH", json: body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["report-schedules"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const deleteSchedule = useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/report-schedules/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["report-schedules"] });
      toast.success("Schedule removed");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const testSmtp = useMutation({
    mutationFn: () => apiFetch<{ message: string }>("/report-schedules/test-email", { method: "POST" }),
    onSuccess: (r) => toast.success(r.message),
    onError: (e: Error) => toast.error(e.message),
  });

  const prefs = data?.notification_prefs ?? { email_alerts: true, push_alerts: false };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">Workspace preferences and demo tools.</p>
      </div>
      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="text-base">Notifications</CardTitle>
          <CardDescription>
            Preferences are stored on your account and apply across sessions.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="email">Email alerts</Label>
            <Switch
              id="email"
              checked={prefs.email_alerts}
              onCheckedChange={(v) => patch.mutate({ ...prefs, email_alerts: v })}
            />
          </div>
          <div className="flex items-center justify-between">
            <Label htmlFor="push">Push alerts</Label>
            <Switch
              id="push"
              checked={prefs.push_alerts}
              onCheckedChange={(v) => patch.mutate({ ...prefs, push_alerts: v })}
            />
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="text-base">Scheduled digest reports</CardTitle>
          <CardDescription>
            Celery Beat runs every 15 minutes. Turn the schedule On to generate and email digests. Set run time in UTC
            for daily, twice-daily, and weekly schedules (hourly uses interval only). PDFs are saved under{" "}
            <code className="text-xs">REPORTS_DIR</code>. Configure <code className="text-xs">SMTP_*</code> for delivery.
            Medium-and-above includes high and critical; use High and critical for escalations only.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <ScheduleCreateForm
            defaultEmail={me?.email ?? ""}
            onCreate={(b) => createSchedule.mutate(b)}
            busy={createSchedule.isPending}
          />
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" size="sm" onClick={() => testSmtp.mutate()} disabled={testSmtp.isPending}>
              Send SMTP test email
            </Button>
          </div>
          {schedules.length === 0 ? (
            <p className="text-sm text-muted-foreground">No schedules yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Severity ≥</TableHead>
                  <TableHead>Cadence</TableHead>
                  <TableHead>Time (UTC)</TableHead>
                  <TableHead>Day</TableHead>
                  <TableHead>Recipient</TableHead>
                  <TableHead>On</TableHead>
                  <TableHead>Last run</TableHead>
                  <TableHead className="w-[72px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {schedules.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell>{severityScheduleLabel(s.min_severity)}</TableCell>
                    <TableCell>{frequencyScheduleLabel(s.frequency)}</TableCell>
                    <TableCell className="min-w-[100px]">
                      <Input
                        type="time"
                        className="h-8 text-xs"
                        defaultValue={hhmmSchedule(s.preferred_time_utc)}
                        key={`pt-${s.id}-${s.preferred_time_utc ?? "none"}`}
                        title="Empty = legacy any-time mode"
                        onBlur={(e) => {
                          const raw = e.target.value;
                          const next = raw === "" ? null : raw;
                          if (next === s.preferred_time_utc) return;
                          patchSchedule.mutate({ id: s.id, body: { preferred_time_utc: next } });
                        }}
                      />
                    </TableCell>
                    <TableCell className="min-w-[88px]">
                      {s.frequency === "weekly" ? (
                        <Select
                          value={String(s.weekly_day_utc ?? 0)}
                          onValueChange={(v) =>
                            patchSchedule.mutate({ id: s.id, body: { weekly_day_utc: Number(v) } })
                          }
                        >
                          <SelectTrigger className="h-8 text-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {WEEKDAY_OPTIONS.map((o) => (
                              <SelectItem key={o.value} value={o.value}>
                                {o.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="max-w-[140px] truncate text-xs">{s.recipient_email}</TableCell>
                    <TableCell>
                      <Switch
                        checked={s.enabled}
                        onCheckedChange={(v) => patchSchedule.mutate({ id: s.id, body: { enabled: v } })}
                      />
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                      {s.last_run_at ? new Date(s.last_run_at).toLocaleString() : "—"}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive"
                        onClick={() => deleteSchedule.mutate(s.id)}
                        disabled={deleteSchedule.isPending}
                      >
                        Remove
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="text-base">Demo data</CardTitle>
          <CardDescription>{data?.demo_mode_hint}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
          <Button
            variant="secondary"
            onClick={async () => {
              try {
                await apiFetch("/events/synthetic?count=80", { method: "POST" });
                toast.success("Synthetic events ingested");
                qc.invalidateQueries();
              } catch (e) {
                toast.error(e instanceof Error ? e.message : "Failed");
              }
            }}
          >
            Random synthetic batch
          </Button>
          <Button
            className="bg-cyan-600 text-primary-foreground hover:bg-cyan-500"
            onClick={async () => {
              try {
                await apiFetch("/events/synthetic?strong=true", { method: "POST" });
                toast.success("Full SOC demo scenario ingested (check Alerts & Incidents)");
                qc.invalidateQueries();
              } catch (e) {
                toast.error(e instanceof Error ? e.message : "Failed");
              }
            }}
          >
            Full SOC demo scenario
          </Button>
        </CardContent>
      </Card>

      <ResetDataCard />
    </div>
  );
}

function ScheduleCreateForm({
  defaultEmail,
  onCreate,
  busy,
}: {
  defaultEmail: string;
  onCreate: (b: {
    min_severity: Severity;
    frequency: ReportSchedule["frequency"];
    recipient_email: string;
    enabled: boolean;
    preferred_time_utc: string | null;
    weekly_day_utc: number | null;
  }) => void;
  busy: boolean;
}) {
  const [minSeverity, setMinSeverity] = React.useState<Severity>("medium");
  const [frequency, setFrequency] = React.useState<ReportSchedule["frequency"]>("daily");
  const [timeUtc, setTimeUtc] = React.useState("09:00");
  const [weeklyDay, setWeeklyDay] = React.useState(0);
  const [recipientEmail, setRecipientEmail] = React.useState(defaultEmail);
  const [enabled, setEnabled] = React.useState(true);

  React.useEffect(() => {
    if (defaultEmail && !recipientEmail) setRecipientEmail(defaultEmail);
  }, [defaultEmail, recipientEmail]);

  return (
    <form
      className="space-y-4 rounded-lg border border-border/50 p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (!recipientEmail.trim()) {
          toast.error("Recipient email required");
          return;
        }
        onCreate({
          min_severity: minSeverity,
          frequency,
          recipient_email: recipientEmail.trim(),
          enabled,
          preferred_time_utc: timeUtc.trim() === "" ? null : timeUtc.trim(),
          weekly_day_utc: frequency === "weekly" ? weeklyDay : null,
        });
      }}
    >
      <p className="text-sm font-medium">New schedule</p>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Minimum severity</Label>
          <Select value={minSeverity} onValueChange={(v) => setMinSeverity(v as Severity)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="low">All severities</SelectItem>
              <SelectItem value="medium">Medium and above</SelectItem>
              <SelectItem value="high">High and critical</SelectItem>
              <SelectItem value="critical">Critical only</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Frequency</Label>
          <Select value={frequency} onValueChange={(v) => setFrequency(v as ReportSchedule["frequency"])}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="hourly">Hourly</SelectItem>
              <SelectItem value="twice_daily">Every 12 hours</SelectItem>
              <SelectItem value="daily">Daily</SelectItem>
              <SelectItem value="weekly">Weekly</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="sched-time">Run time (UTC)</Label>
          <Input id="sched-time" type="time" value={timeUtc} onChange={(e) => setTimeUtc(e.target.value)} step={60} />
          <p className="text-xs text-muted-foreground">
            Used for daily, twice-daily, and weekly. Hourly ignores this. Clear for legacy any-time mode (interval only).
          </p>
        </div>
        {frequency === "weekly" && (
          <div className="space-y-2 sm:col-span-2">
            <Label>Weekday (UTC)</Label>
            <Select value={String(weeklyDay)} onValueChange={(v) => setWeeklyDay(Number(v))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {WEEKDAY_OPTIONS.map((o) => (
                  <SelectItem key={o.value} value={o.value}>
                    {o.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>
      <div className="space-y-2">
        <Label htmlFor="recip">Recipient email</Label>
        <Input
          id="recip"
          type="email"
          value={recipientEmail}
          onChange={(e) => setRecipientEmail(e.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
        />
      </div>
      <div className="flex items-center justify-between">
        <Label htmlFor="sched-on">Enabled</Label>
        <Switch id="sched-on" checked={enabled} onCheckedChange={setEnabled} />
      </div>
      <Button type="submit" disabled={busy}>
        Add schedule
      </Button>
    </form>
  );
}

function ResetDataCard() {
  const qc = useQueryClient();
  const [confirmed, setConfirmed] = React.useState(false);

  const reset = useMutation({
    mutationFn: () => apiFetch<{ message: string }>("/settings/reset", { method: "DELETE" }),
    onSuccess: (r) => {
      toast.success(r.message);
      qc.invalidateQueries();
      setConfirmed(false);
    },
    onError: (e: Error) => {
      toast.error(e.message);
      setConfirmed(false);
    },
  });

  return (
    <Card className="border-destructive/30 bg-card/40">
      <CardHeader>
        <CardTitle className="text-base text-destructive">Danger zone</CardTitle>
        <CardDescription>
          Permanently delete all events, alerts, incidents, and reports. Users and schedules are preserved.
          Use this before starting a fresh attack scenario.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!confirmed ? (
          <Button
            variant="destructive"
            onClick={() => setConfirmed(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Reset all data
          </Button>
        ) : (
          <div className="flex items-center gap-3">
            <p className="text-sm text-destructive">This cannot be undone. Are you sure?</p>
            <Button
              variant="destructive"
              disabled={reset.isPending}
              onClick={() => reset.mutate()}
            >
              {reset.isPending ? "Deleting…" : "Yes, delete everything"}
            </Button>
            <Button variant="outline" onClick={() => setConfirmed(false)}>
              Cancel
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
