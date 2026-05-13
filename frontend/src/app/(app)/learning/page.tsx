"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpenCheck, Clock3, GraduationCap, Lightbulb, PlayCircle, Target } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { apiFetch } from "@/lib/api/client";
import type {
  Alert,
  ExerciseActionType,
  DoctorCoachResponse,
  ExerciseScenario,
  ExerciseSession,
  Paginated,
} from "@/lib/api/types";

type StartPayload = { scenario_id: string; duration_minutes: number };
type ActionPayload = {
  action_type: ExerciseActionType;
  target_type?: string;
  target_id?: number;
  notes?: string;
};

export default function LearningPage() {
  const qc = useQueryClient();
  const [duration, setDuration] = useState(10);
  const [selectedScenario, setSelectedScenario] = useState<string>("");
  const [actionTarget, setActionTarget] = useState<string>("");
  const [actionNotes, setActionNotes] = useState<string>("");
  const [doctorQuestion, setDoctorQuestion] = useState("");
  const [doctorLanguage, setDoctorLanguage] = useState<"en" | "ar">("en");

  const normalizeDuration = (value: number): number => {
    if (!Number.isFinite(value)) return 10;
    return Math.min(120, Math.max(5, Math.trunc(value)));
  };

  const scenariosQuery = useQuery({
    queryKey: ["learning-scenarios"],
    queryFn: () => apiFetch<ExerciseScenario[]>("/learning/scenarios"),
  });
  const selectedScenarioId = selectedScenario || (scenariosQuery.data ?? [])[0]?.id || "";
  const sessionsQuery = useQuery({
    queryKey: ["learning-sessions"],
    queryFn: () => apiFetch<Paginated<ExerciseSession>>("/learning/sessions?page=1&page_size=10"),
  });

  const latestSession = useMemo(
    () => sessionsQuery.data?.items.find((s) => s.status === "active") ?? sessionsQuery.data?.items[0],
    [sessionsQuery.data?.items],
  );
  const activeSession = useMemo(
    () => sessionsQuery.data?.items.find((s) => s.status === "active") ?? null,
    [sessionsQuery.data?.items],
  );

  const startMutation = useMutation({
    mutationFn: (payload: StartPayload) =>
      apiFetch<ExerciseSession>("/learning/sessions", { method: "POST", json: payload }),
    onSuccess: () => {
      toast.success("Exercise started");
      qc.invalidateQueries({ queryKey: ["learning-sessions"] });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const actionMutation = useMutation({
    mutationFn: ({ sessionId, payload }: { sessionId: number; payload: ActionPayload }) =>
      apiFetch<ExerciseSession>(`/learning/sessions/${sessionId}/actions`, {
        method: "POST",
        json: payload,
      }),
    onSuccess: () => {
      toast.success("Action recorded");
      setActionNotes("");
      qc.invalidateQueries({ queryKey: ["learning-sessions"] });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const hintMutation = useMutation({
    mutationFn: (sessionId: number) =>
      apiFetch<{ message: string }>(`/learning/sessions/${sessionId}/hint`, { method: "POST" }),
    onSuccess: (res) => {
      toast.success(res.message);
      qc.invalidateQueries({ queryKey: ["learning-sessions"] });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const completeMutation = useMutation({
    mutationFn: (sessionId: number) =>
      apiFetch<ExerciseSession>(`/learning/sessions/${sessionId}/complete`, { method: "POST" }),
    onSuccess: () => {
      toast.success("Exercise completed and graded");
      qc.invalidateQueries({ queryKey: ["learning-sessions"] });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const sessionAlertsQuery = useQuery({
    queryKey: ["learning-session-alerts", activeSession?.id, activeSession?.started_at],
    enabled: !!activeSession,
    queryFn: () => {
      if (!activeSession) {
        return Promise.resolve({ items: [], total: 0, page: 1, page_size: 10 } as Paginated<Alert>);
      }
      const params = new URLSearchParams({
        page: "1",
        page_size: "10",
        from_ts: activeSession.started_at,
        to_ts: new Date().toISOString(),
      });
      return apiFetch<Paginated<Alert>>(`/alerts?${params.toString()}`);
    },
  });

  const patchAlertStatusMutation = useMutation({
    mutationFn: ({ alertId, status }: { alertId: number; status: "acknowledged" | "resolved" }) =>
      apiFetch<Alert>(`/alerts/${alertId}/status`, {
        method: "PATCH",
        json: { status },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["learning-session-alerts"] });
      qc.invalidateQueries({ queryKey: ["learning-sessions"] });
      toast.success("Alert status updated");
    },
    onError: (error: Error) => toast.error(error.message),
  });
  const doctorModeMutation = useMutation({
    mutationFn: (payload: { sessionId: number; question: string; language: "en" | "ar" }) =>
      apiFetch<DoctorCoachResponse>("/learning/doctor-mode", {
        method: "POST",
        json: {
          session_id: payload.sessionId,
          question: payload.question,
          language: payload.language,
        },
      }),
    onError: (error: Error) => toast.error(error.message),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Student Learning Lab</h1>
        <p className="text-sm text-muted-foreground">
          Run timed SOC exercises, log your response actions, and review your scored performance.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-border/60 bg-card/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <PlayCircle className="h-4 w-4 text-cyan-400" />
              Start Exercise
            </CardTitle>
            <CardDescription>Pick a scenario and duration to begin a timed SOC drill.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-2">
              {(scenariosQuery.data ?? []).map((scenario) => (
                <button
                  key={scenario.id}
                  onClick={() => setSelectedScenario(scenario.id)}
                  className={`rounded-lg border px-3 py-2 text-left transition-colors ${
                    selectedScenarioId === scenario.id
                      ? "border-cyan-500/40 bg-cyan-500/10"
                      : "border-border/50 hover:bg-muted/30"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{scenario.name}</span>
                    <Badge variant="outline" className="capitalize">
                      {scenario.severity}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{scenario.description}</p>
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <Clock3 className="h-4 w-4 text-muted-foreground" />
              <Input
                type="number"
                value={duration}
                min={5}
                max={120}
                onChange={(e) => setDuration(normalizeDuration(Number(e.target.value)))}
                className="w-28"
              />
              <span className="text-sm text-muted-foreground">minutes</span>
            </div>
            <Button
              onClick={() => {
                if (!selectedScenarioId) {
                  toast.error("Pick a scenario first");
                  return;
                }
                const safeDuration = normalizeDuration(duration);
                if (safeDuration !== duration) {
                  setDuration(safeDuration);
                  toast.error("Duration must be between 5 and 120 minutes.");
                  return;
                }
                startMutation.mutate({
                  scenario_id: selectedScenarioId,
                  duration_minutes: safeDuration,
                });
              }}
              disabled={startMutation.isPending || (scenariosQuery.data ?? []).length === 0}
              className="w-full"
            >
              Launch Timed Exercise
            </Button>
          </CardContent>
        </Card>

        <Card className="border-border/60 bg-card/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <GraduationCap className="h-4 w-4 text-violet-400" />
              Active Session Controls
            </CardTitle>
            <CardDescription>
              Record investigation actions to influence your grading outcome.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {!latestSession ? (
              <p className="text-sm text-muted-foreground">No sessions yet.</p>
            ) : (
              <>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <Badge variant="outline">{latestSession.scenario_id}</Badge>
                  <Badge variant="secondary" className="capitalize">
                    {latestSession.status}
                  </Badge>
                  <span className="text-muted-foreground">
                    Ends: {new Date(latestSession.ends_at).toLocaleTimeString()}
                  </span>
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder="Target ID (alert/incident)"
                    value={actionTarget}
                    onChange={(e) => setActionTarget(e.target.value)}
                    className="w-48"
                  />
                  <Input
                    placeholder="Notes (optional)"
                    value={actionNotes}
                    onChange={(e) => setActionNotes(e.target.value)}
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="outline"
                    disabled={latestSession.status !== "active"}
                    onClick={() =>
                      actionMutation.mutate({
                        sessionId: latestSession.id,
                        payload: {
                          action_type: "acknowledge_alert",
                          target_type: "alert",
                          target_id: Number(actionTarget) || undefined,
                          notes: actionNotes || undefined,
                        },
                      })
                    }
                  >
                    Acknowledge Alert
                  </Button>
                  <Button
                    variant="outline"
                    disabled={latestSession.status !== "active"}
                    onClick={() =>
                      actionMutation.mutate({
                        sessionId: latestSession.id,
                        payload: {
                          action_type: "resolve_alert",
                          target_type: "alert",
                          target_id: Number(actionTarget) || undefined,
                          notes: actionNotes || undefined,
                        },
                      })
                    }
                  >
                    Resolve Alert
                  </Button>
                  <Button
                    variant="outline"
                    disabled={latestSession.status !== "active"}
                    onClick={() =>
                      actionMutation.mutate({
                        sessionId: latestSession.id,
                        payload: {
                          action_type: "escalate_incident",
                          target_type: "incident",
                          target_id: Number(actionTarget) || undefined,
                          notes: actionNotes || undefined,
                        },
                      })
                    }
                  >
                    Escalate Incident
                  </Button>
                  <Button
                    variant="outline"
                    disabled={latestSession.status !== "active"}
                    onClick={() =>
                      actionMutation.mutate({
                        sessionId: latestSession.id,
                        payload: {
                          action_type: "add_note",
                          notes: actionNotes || "Analyst note added",
                        },
                      })
                    }
                  >
                    Add Note
                  </Button>
                </div>
                <div className="space-y-2 rounded-md border border-border/50 p-2">
                  <p className="text-xs font-medium text-muted-foreground">
                    Live session alerts ({sessionAlertsQuery.data?.total ?? 0})
                  </p>
                  {(sessionAlertsQuery.data?.items ?? []).length === 0 ? (
                    <p className="text-xs text-muted-foreground">
                      No alerts in this session window yet. Launch a scenario to generate telemetry.
                    </p>
                  ) : (
                    (sessionAlertsQuery.data?.items ?? []).map((alert) => (
                      <div
                        key={alert.id}
                        className="rounded-md border border-border/40 bg-muted/20 px-2 py-1.5"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <p className="truncate text-xs font-medium">
                            #{alert.id} {alert.title}
                          </p>
                          <Badge variant="outline" className="text-[10px] capitalize">
                            {alert.severity}
                          </Badge>
                        </div>
                        <div className="mt-1 flex items-center justify-between">
                          <p className="text-[11px] text-muted-foreground capitalize">
                            Status: {alert.status}
                          </p>
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-6 px-2 text-[10px]"
                              disabled={alert.status !== "new" || patchAlertStatusMutation.isPending}
                              onClick={() =>
                                patchAlertStatusMutation.mutate({
                                  alertId: alert.id,
                                  status: "acknowledged",
                                })
                              }
                            >
                              Ack
                            </Button>
                            <Button
                              size="sm"
                              className="h-6 px-2 text-[10px]"
                              disabled={patchAlertStatusMutation.isPending}
                              onClick={() =>
                                patchAlertStatusMutation.mutate({
                                  alertId: alert.id,
                                  status: "resolved",
                                })
                              }
                            >
                              Resolve
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    onClick={() => hintMutation.mutate(latestSession.id)}
                    disabled={latestSession.status !== "active"}
                    className="flex-1"
                  >
                    <Lightbulb className="mr-1 h-4 w-4" />
                    Request Hint
                  </Button>
                  <Button
                    onClick={() => completeMutation.mutate(latestSession.id)}
                    disabled={latestSession.status !== "active"}
                    className="flex-1"
                  >
                    Complete & Grade
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BookOpenCheck className="h-4 w-4 text-emerald-400" />
            Performance Dashboard
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {(sessionsQuery.data?.items ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">Complete your first exercise to see progression.</p>
          ) : (
            sessionsQuery.data?.items.map((session) => (
              <div key={session.id} className="rounded-lg border border-border/50 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Target className="h-4 w-4 text-cyan-400" />
                    <p className="text-sm font-medium">
                      Session #{session.id} · {session.scenario_id}
                    </p>
                    <Badge variant="outline" className="capitalize">
                      {session.status}
                    </Badge>
                  </div>
                  <p className="text-sm font-semibold text-foreground">
                    Score: {session.overall_score?.toFixed(1) ?? "—"}
                  </p>
                </div>
                <Separator className="my-2" />
                <div className="grid gap-2 text-xs sm:grid-cols-4">
                  <p>Detection: {session.detection_score?.toFixed(1) ?? "—"}</p>
                  <p>Analysis: {session.analysis_score?.toFixed(1) ?? "—"}</p>
                  <p>Response: {session.response_score?.toFixed(1) ?? "—"}</p>
                  <p>Reporting: {session.reporting_score?.toFixed(1) ?? "—"}</p>
                </div>
                <div className="mt-2 grid gap-1 text-xs text-muted-foreground">
                  <p>
                    <span className="font-medium text-foreground">Strengths:</span>{" "}
                    {session.strengths ?? "—"}
                  </p>
                  <p>
                    <span className="font-medium text-foreground">Weaknesses:</span>{" "}
                    {session.weaknesses ?? "—"}
                  </p>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="text-base">Doctor Teacher Mode</CardTitle>
          <CardDescription>
            Ask for coaching feedback based on your latest session performance.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant={doctorLanguage === "en" ? "default" : "outline"}
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => setDoctorLanguage("en")}
            >
              English
            </Button>
            <Button
              type="button"
              variant={doctorLanguage === "ar" ? "default" : "outline"}
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => setDoctorLanguage("ar")}
            >
              Arabic
            </Button>
          </div>
          <Input
            placeholder="Example: How should I prioritize alerts before escalation?"
            value={doctorQuestion}
            onChange={(e) => setDoctorQuestion(e.target.value)}
          />
          <Button
            disabled={!latestSession || doctorQuestion.trim().length < 3 || doctorModeMutation.isPending}
            onClick={() =>
              latestSession &&
              doctorModeMutation.mutate({
                sessionId: latestSession.id,
                question: doctorQuestion.trim(),
                language: doctorLanguage,
              })
            }
          >
            Get coaching
          </Button>
          {doctorModeMutation.data && (
            <div className="space-y-2 rounded-md border border-cyan-500/20 bg-cyan-500/5 p-3 text-sm">
              <p className="font-medium text-cyan-300">Diagnosis</p>
              <p className="text-muted-foreground">{doctorModeMutation.data.diagnosis}</p>
              <p className="font-medium text-cyan-300">Likely gap</p>
              <p className="text-muted-foreground">{doctorModeMutation.data.likely_gap}</p>
              <p className="font-medium text-cyan-300">Coaching steps</p>
              <ul className="space-y-1 text-muted-foreground">
                {doctorModeMutation.data.coaching_steps.map((step) => (
                  <li key={step}>- {step}</li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
