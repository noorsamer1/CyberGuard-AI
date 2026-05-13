"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Database,
  FlaskConical,
  Info,
  Network,
  RotateCcw,
  Shield,
  Terminal,
  X,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { AttackLabRangeTerminal } from "@/components/attack-lab/attack-lab-range-terminal";
import { apiFetch } from "@/lib/api/client";
import { cn } from "@/lib/utils";

type LabMode = "synthetic" | "range";

interface SyntheticScenario {
  id: string;
  name: string;
  description: string;
  severity: string;
  mitre_tactics: string[];
  mitre_techniques: string[];
  threat_actor: string;
  estimated_alerts: number;
  duration_minutes: number;
}

interface SyntheticRunResult {
  scenario_id: string;
  name: string;
  events_ingested: number;
  message: string;
}

interface RangeStatus {
  enabled: boolean;
  target_url: string;
  public_url: string;
  healthy: boolean;
  message: string;
  range_target_hostname: string;
  range_target_ip: string | null;
  api_runner_hostname: string | null;
}

interface RangeScenario {
  id: string;
  name: string;
  description: string;
  severity: string;
  mitre_tactics: string[];
  mitre_techniques: string[];
  execution_mode: "local_range";
  target_url: string;
  cli_examples: string[];
  safety_notes: string[];
  expected_detections: string[];
}

interface RangeRunResult {
  scenario_id: string;
  name: string;
  requests_executed: number;
  logs_collected: number;
  events_ingested: number;
  alerts_generated: number;
  incidents_created: number;
  message: string;
}

const SYNTHETIC_SCENARIOS: SyntheticScenario[] = [
  {
    id: "ssh_brute_force",
    name: "SSH Brute Force Campaign",
    description: "Injects synthetic SSH authentication failures and a successful access event.",
    severity: "high",
    mitre_tactics: ["Credential Access"],
    mitre_techniques: ["T1110.003"],
    threat_actor: "Generic opportunistic attacker",
    estimated_alerts: 1,
    duration_minutes: 5,
  },
  {
    id: "port_scan_exploit",
    name: "Reconnaissance & Service Exploitation",
    description: "Injects synthetic port scan and web exploitation telemetry.",
    severity: "high",
    mitre_tactics: ["Discovery", "Initial Access"],
    mitre_techniques: ["T1046", "T1190"],
    threat_actor: "Opportunistic threat actor",
    estimated_alerts: 1,
    duration_minutes: 3,
  },
  {
    id: "credential_stuffing",
    name: "Credential Stuffing Attack",
    description: "Injects low-and-slow failed logins against multiple usernames.",
    severity: "medium",
    mitre_tactics: ["Credential Access"],
    mitre_techniques: ["T1110.004"],
    threat_actor: "Cybercrime group with credential database",
    estimated_alerts: 2,
    duration_minutes: 5,
  },
  {
    id: "ransomware_chain",
    name: "Ransomware Kill Chain",
    description: "Injects synthetic recon, lateral movement, payload, and impact signals.",
    severity: "critical",
    mitre_tactics: ["Discovery", "Lateral Movement", "Impact"],
    mitre_techniques: ["T1046", "T1021.001", "T1486"],
    threat_actor: "Ransomware-as-a-Service operator",
    estimated_alerts: 2,
    duration_minutes: 10,
  },
  {
    id: "data_exfiltration",
    name: "Insider Data Exfiltration",
    description: "Injects synthetic DLP access and outbound transfer telemetry.",
    severity: "high",
    mitre_tactics: ["Collection", "Exfiltration"],
    mitre_techniques: ["T1560", "T1048"],
    threat_actor: "Malicious insider / compromised contractor",
    estimated_alerts: 1,
    duration_minutes: 6,
  },
  {
    id: "apt_lateral_movement",
    name: "APT Lateral Movement Campaign",
    description: "Injects synthetic valid-account, persistence, discovery, and SMB movement signals.",
    severity: "critical",
    mitre_tactics: ["Initial Access", "Persistence", "Discovery", "Lateral Movement"],
    mitre_techniques: ["T1078", "T1053", "T1018", "T1021"],
    threat_actor: "Advanced Persistent Threat",
    estimated_alerts: 2,
    duration_minutes: 15,
  },
];

const SEVERITY_CLASSES: Record<string, string> = {
  low: "border-emerald-500/20 bg-emerald-500/15 text-emerald-400",
  medium: "border-amber-500/20 bg-amber-500/15 text-amber-400",
  high: "border-orange-500/20 bg-orange-500/15 text-orange-400",
  critical: "border-red-500/20 bg-red-600/20 text-red-400",
};

const ICONS: Record<string, typeof FlaskConical> = {
  range_brute_force: Shield,
  range_sql_injection: Terminal,
  range_path_traversal: Network,
  range_exfiltration: Database,
  range_ransomware: Zap,
  range_port_scan: Network,
};

function invalidateSoc(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["alerts"] });
  qc.invalidateQueries({ queryKey: ["incidents"] });
  qc.invalidateQueries({ queryKey: ["events"] });
  qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
  qc.invalidateQueries({ queryKey: ["dashboard-charts"] });
}

function ResultModal({
  title,
  mode,
  result,
  isBusy,
  rangeStatus,
  rangeScenarioId,
  rangeTerminalLaunchKey,
  onClose,
}: {
  title: string;
  mode: LabMode;
  result: SyntheticRunResult | RangeRunResult | null;
  isBusy: boolean;
  rangeStatus: RangeStatus | undefined;
  /** Cyber range scenario id, or manual_collect for log drain; null for synthetic. */
  rangeScenarioId: string | null;
  rangeTerminalLaunchKey: number;
  onClose: () => void;
}) {
  const range = result && "requests_executed" in result ? result : null;
  const synthetic = result && "events_ingested" in result && !("requests_executed" in result) ? result : null;
  const publicUrl = rangeStatus?.public_url ?? "http://127.0.0.1:8088";
  const internalUrl = rangeStatus?.target_url ?? "http://range-target:8088";
  const dockerHost = rangeStatus?.range_target_hostname ?? "range-target";
  const dockerIp = rangeStatus?.range_target_ip;
  const runnerHost = rangeStatus?.api_runner_hostname;

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 18 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="attack-lab-console-title"
    >
      <Card className="max-h-[90vh] w-full max-w-3xl overflow-y-auto border-cyan-500/30 bg-[#080d12] shadow-2xl shadow-cyan-950/40">
        <CardHeader className="flex flex-row items-start justify-between border-b border-white/10">
          <div>
            <CardTitle id="attack-lab-console-title" className="flex items-center gap-2 text-cyan-200">
              <Terminal className="h-4 w-4" />
              Console simulation — {title}
            </CardTitle>
            <CardDescription>
              {mode === "range"
                ? "Live traffic against the disposable range container; logs drain into CyberGuard ingestion."
                : "Synthetic bundle posted to the scenarios API (no range Docker required)."}
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close console">
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4 p-5 text-xs">
          {mode === "range" ? (
            <div className="rounded-md border border-cyan-500/25 bg-cyan-500/5 p-3 font-sans leading-relaxed text-cyan-100/90">
              <p className="font-semibold text-cyan-200">Where this attack runs</p>
              <ul className="mt-2 list-inside list-disc space-y-1 text-[11px] text-muted-foreground">
                <li>
                  The vulnerable app lives in a <span className="text-foreground">Docker</span> service named{" "}
                  <code className="rounded bg-black/40 px-1 py-0.5 font-mono text-cyan-300">{dockerHost}</code> on the
                  compose network. From your browser you reach it as{" "}
                  <code className="rounded bg-black/40 px-1 font-mono text-cyan-300">{publicUrl}</code> (published
                  port).
                </li>
                <li>
                  The CyberGuard API container calls the same target internally at{" "}
                  <code className="rounded bg-black/40 px-1 font-mono text-cyan-300">{internalUrl}</code>
                  {dockerIp ? (
                    <>
                      {" "}
                      (resolved IP from API:{" "}
                      <code className="rounded bg-black/40 px-1 font-mono text-cyan-300">{dockerIp}</code>).
                    </>
                  ) : (
                    <> (DNS IP varies per Docker bridge; check with docker inspect on your host).</>
                  )}
                </li>
                {runnerHost ? (
                  <li>
                    Scenario runner host:{" "}
                    <code className="rounded bg-black/40 px-1 font-mono text-cyan-300">{runnerHost}</code> — HTTP
                    requests originate here, not from your laptop.
                  </li>
                ) : null}
              </ul>
            </div>
          ) : (
            <div className="rounded-md border border-amber-500/25 bg-amber-500/5 p-3 font-sans leading-relaxed text-amber-100/90">
              <p className="font-semibold text-amber-200">Synthetic mode</p>
              <p className="mt-1 text-[11px] text-muted-foreground">
                No Docker range traffic: the backend builds a telemetry bundle and ingests it as if it arrived from
                sensors. Use Cyber Range mode to hit the real{" "}
                <code className="rounded bg-black/40 px-1 font-mono text-amber-200/90">range-target</code> container.
              </p>
            </div>
          )}
          {mode === "range" && rangeScenarioId ? (
            <AttackLabRangeTerminal
              launchKey={rangeTerminalLaunchKey}
              scenarioId={rangeScenarioId}
              scenarioName={title}
              publicUrl={publicUrl}
              targetUrl={internalUrl}
              dockerHost={dockerHost}
              dockerIp={dockerIp ?? null}
              runnerHost={runnerHost ?? null}
              isBusy={isBusy}
              result={range}
            />
          ) : (
            <div className="rounded-md border border-cyan-500/20 bg-black/50 p-4 font-mono">
              <p className="text-cyan-300">cyberguard@attack-lab:~$ run {mode}</p>
              {isBusy && !result ? (
                <p className="mt-2 animate-pulse text-muted-foreground">Executing scenario against backend…</p>
              ) : null}
              {result ? (
                <div className="mt-3 space-y-1 text-muted-foreground">
                  <p className="text-green-400">[ok] {result.message}</p>
                  {synthetic && <p>events_ingested={synthetic.events_ingested}</p>}
                </div>
              ) : null}
              {!isBusy && !result ? (
                <p className="mt-2 text-rose-300">No result (request may have failed — check the toast).</p>
              ) : null}
            </div>
          )}
          <div className="flex justify-end gap-2">
            <Link href="/alerts" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
              View Alerts
            </Link>
            <Link href="/incidents" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
              View Incidents
            </Link>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function AttackLabPage() {
  const qc = useQueryClient();
  const [mode, setMode] = useState<LabMode>("range");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [modalTitle, setModalTitle] = useState("");
  const [modalMode, setModalMode] = useState<LabMode>("range");
  const [modalResult, setModalResult] = useState<SyntheticRunResult | RangeRunResult | null>(null);
  const [simulationOpen, setSimulationOpen] = useState(false);
  /** Range scenario id for terminal script, or manual_collect; null when synthetic. */
  const [modalRangeScenarioId, setModalRangeScenarioId] = useState<string | null>(null);
  const [rangeTerminalLaunchKey, setRangeTerminalLaunchKey] = useState(0);

  const rangeStatus = useQuery({
    queryKey: ["range-status"],
    queryFn: () => apiFetch<RangeStatus>("/range/status"),
  });

  const rangeScenarios = useQuery({
    queryKey: ["range-scenarios"],
    queryFn: () => apiFetch<RangeScenario[]>("/range/scenarios"),
  });

  const closeConsole = () => {
    setSimulationOpen(false);
    setModalResult(null);
    setModalRangeScenarioId(null);
  };

  const syntheticLaunch = useMutation({
    mutationFn: (scenarioId: string) =>
      apiFetch<SyntheticRunResult>(`/scenarios/${scenarioId}/run`, { method: "POST" }),
    onSuccess: (result) => {
      setModalResult(result);
      invalidateSoc(qc);
      toast.success("Synthetic scenario launched");
    },
    onError: (e: Error) => {
      toast.error(e.message);
      setModalResult(null);
      setSimulationOpen(false);
    },
  });

  const rangeLaunch = useMutation({
    mutationFn: (scenarioId: string) =>
      apiFetch<RangeRunResult>(`/range/scenarios/${scenarioId}/run`, { method: "POST" }),
    onSuccess: (result) => {
      setModalResult(result);
      invalidateSoc(qc);
      toast.success("Cyber range scenario completed");
    },
    onError: (e: Error) => {
      toast.error(e.message);
      setModalResult(null);
      setSimulationOpen(false);
    },
  });

  const collectLogs = useMutation({
    mutationFn: () => apiFetch<RangeRunResult>("/range/collect", { method: "POST" }),
    onMutate: () => {
      setSimulationOpen(true);
      setModalTitle("Manual Range Log Collection");
      setModalMode("range");
      setModalResult(null);
      setModalRangeScenarioId("manual_collect");
      setRangeTerminalLaunchKey((k) => k + 1);
    },
    onSuccess: (result) => {
      setModalResult(result);
      invalidateSoc(qc);
      toast.success("Range logs collected");
    },
    onError: (e: Error) => {
      toast.error(e.message);
      setModalResult(null);
      setSimulationOpen(false);
    },
  });

  const resetRange = useMutation({
    mutationFn: () => apiFetch<RangeRunResult>("/range/reset", { method: "POST" }),
    onSuccess: () => {
      rangeStatus.refetch();
      toast.success("Local range target reset");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const consoleBusy =
    syntheticLaunch.isPending || rangeLaunch.isPending || collectLogs.isPending;

  const openSynthetic = (scenario: SyntheticScenario) => {
    setSimulationOpen(true);
    void rangeStatus.refetch();
    setModalTitle(scenario.name);
    setModalMode("synthetic");
    setModalResult(null);
    setModalRangeScenarioId(null);
    syntheticLaunch.mutate(scenario.id);
  };

  const openRange = (scenario: RangeScenario) => {
    setSimulationOpen(true);
    void rangeStatus.refetch();
    setModalTitle(scenario.name);
    setModalMode("range");
    setModalResult(null);
    setModalRangeScenarioId(scenario.id);
    setRangeTerminalLaunchKey((k) => k + 1);
    rangeLaunch.mutate(scenario.id);
  };

  const rangeHealthy = rangeStatus.data?.healthy ?? false;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Attack Lab</h1>
          <p className="text-sm text-muted-foreground">
            Run safe teaching scenarios as synthetic telemetry or against a local controlled cyber range.
          </p>
        </div>
        <div className="flex rounded-lg border border-border/70 bg-muted/20 p-1">
          <Button
            variant={mode === "range" ? "default" : "ghost"}
            size="sm"
            onClick={() => setMode("range")}
          >
            Cyber Range
          </Button>
          <Button
            variant={mode === "synthetic" ? "default" : "ghost"}
            size="sm"
            onClick={() => setMode("synthetic")}
          >
            Synthetic Demo
          </Button>
        </div>
      </div>

      {mode === "range" ? (
        <>
          <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
            <div className="flex items-start gap-3 rounded-lg border border-cyan-500/20 bg-cyan-500/10 px-4 py-3">
              <Shield className="mt-0.5 h-4 w-4 shrink-0 text-cyan-300" />
              <div className="space-y-1 text-xs">
                <p className="font-medium text-cyan-200">Controlled local cyber range</p>
                <p className="text-cyan-100/80">
                  Real local requests hit an intentionally vulnerable Docker target bound to localhost only.
                  No arbitrary targets, no public systems, and no host files are touched.
                </p>
                <p className="font-mono text-[11px] text-cyan-100/70">
                  browser→{rangeStatus.data?.public_url ?? "http://127.0.0.1:8088"} api→
                  {rangeStatus.data?.target_url ?? "http://range-target:8088"} service=
                  {rangeStatus.data?.range_target_hostname ?? "range-target"}
                  {rangeStatus.data?.range_target_ip
                    ? ` ip=${rangeStatus.data.range_target_ip}`
                    : ""}{" "}
                  status={rangeHealthy ? "healthy" : "unavailable"}
                </p>
                {rangeStatus.data?.api_runner_hostname ? (
                  <p className="font-mono text-[10px] text-cyan-100/55">
                    api_runner_host={rangeStatus.data.api_runner_hostname}
                  </p>
                ) : null}
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => collectLogs.mutate()} disabled={collectLogs.isPending}>
                <Database className="mr-2 h-4 w-4" />
                Collect Range Logs
              </Button>
              <Button variant="outline" onClick={() => resetRange.mutate()} disabled={resetRange.isPending}>
                <RotateCcw className="mr-2 h-4 w-4" />
                Reset Range
              </Button>
            </div>
          </div>

          {!rangeHealthy && (
            <div className="flex items-center gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
              <p className="text-xs text-amber-300">
                {rangeStatus.data?.message ?? "Range target is not available. Start Docker Compose with range-target enabled."}
              </p>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {(rangeScenarios.data ?? []).map((scenario) => {
              const Icon = ICONS[scenario.id] ?? FlaskConical;
              const open = expandedId === scenario.id;
              return (
                <Card key={scenario.id} className="flex h-full flex-col border-border/60 bg-card/40">
                  <CardHeader className="pb-3">
                    <div className="mb-2 flex items-center gap-2">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-300">
                        <Icon className="h-5 w-5" />
                      </div>
                      <Badge className={cn("border text-[10px] uppercase", SEVERITY_CLASSES[scenario.severity])}>
                        {scenario.severity}
                      </Badge>
                      <Badge variant="outline" className="text-[10px] uppercase">
                        local range
                      </Badge>
                    </div>
                    <CardTitle className="text-sm">{scenario.name}</CardTitle>
                    <CardDescription className="text-xs">{scenario.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="flex flex-1 flex-col gap-3">
                    <div className="flex flex-wrap gap-1">
                      {scenario.mitre_techniques.map((technique) => (
                        <span key={technique} className="rounded border border-cyan-500/20 bg-cyan-500/10 px-1.5 py-0.5 font-mono text-[10px] text-cyan-300">
                          {technique}
                        </span>
                      ))}
                    </div>
                    <p className="font-mono text-[10px] text-muted-foreground">{scenario.target_url}</p>
                    <div className="flex flex-wrap gap-1">
                      {scenario.expected_detections.map((rule) => (
                        <span key={rule} className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                          {rule}
                        </span>
                      ))}
                    </div>
                    <Button variant="ghost" size="sm" className="h-7 justify-start px-2 text-[11px]" onClick={() => setExpandedId(open ? null : scenario.id)}>
                      <Info className="mr-1.5 h-3.5 w-3.5" />
                      {open ? "Hide local CLI notes" : "Show local CLI notes"}
                    </Button>
                    {open && (
                      <div className="space-y-2 rounded-md border border-cyan-500/20 bg-cyan-500/5 p-2">
                        <p className="text-[11px] font-semibold text-cyan-300">Doctor CLI examples</p>
                        {scenario.cli_examples.map((cmd) => (
                          <p key={cmd} className="rounded bg-black/50 px-2 py-1 font-mono text-[10px] text-cyan-100">
                            {cmd}
                          </p>
                        ))}
                        <p className="text-[11px] font-semibold text-cyan-300">Safety notes</p>
                        {scenario.safety_notes.map((note) => (
                          <p key={note} className="text-[10px] text-muted-foreground">
                            - {note}
                          </p>
                        ))}
                      </div>
                    )}
                    <div className="mt-auto pt-1">
                      <Tooltip>
                        <TooltipTrigger
                          render={
                            <Button
                              variant="outline"
                              size="sm"
                              className="w-full"
                              disabled={!rangeHealthy || rangeLaunch.isPending}
                              onClick={() => openRange(scenario)}
                            >
                              Launch in Range
                            </Button>
                          }
                        />
                        <TooltipContent className="max-w-sm text-xs">
                          Executes a fixed local-only scenario against the disposable Docker target.
                        </TooltipContent>
                      </Tooltip>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </>
      ) : (
        <>
          <div className="flex items-center gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3">
            <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
            <p className="text-xs text-amber-300">
              Synthetic mode injects prebuilt telemetry only. It is still useful for demos when Docker range services are not running.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {SYNTHETIC_SCENARIOS.map((scenario) => (
              <Card key={scenario.id} className="flex h-full flex-col border-border/60 bg-card/40">
                <CardHeader>
                  <div className="mb-2 flex items-center gap-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted/60 text-cyan-300">
                      <FlaskConical className="h-5 w-5" />
                    </div>
                    <Badge className={cn("border text-[10px] uppercase", SEVERITY_CLASSES[scenario.severity])}>
                      {scenario.severity}
                    </Badge>
                    <Badge variant="outline" className="text-[10px] uppercase">
                      synthetic
                    </Badge>
                  </div>
                  <CardTitle className="text-sm">{scenario.name}</CardTitle>
                  <CardDescription className="text-xs">{scenario.description}</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col gap-3">
                  <div className="flex flex-wrap gap-1">
                    {scenario.mitre_techniques.map((technique) => (
                      <span key={technique} className="rounded border border-cyan-500/20 bg-cyan-500/10 px-1.5 py-0.5 font-mono text-[10px] text-cyan-300">
                        {technique}
                      </span>
                    ))}
                  </div>
                  <p className="text-[11px] italic text-muted-foreground">{scenario.threat_actor}</p>
                  <div className="mt-auto">
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full"
                      disabled={syntheticLaunch.isPending}
                      onClick={() => openSynthetic(scenario)}
                    >
                      Launch Synthetic Demo
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      <AnimatePresence>
        {simulationOpen && (
          <ResultModal
            title={modalTitle}
            mode={modalMode}
            result={modalResult}
            isBusy={consoleBusy}
            rangeStatus={rangeStatus.data}
            rangeScenarioId={modalRangeScenarioId}
            rangeTerminalLaunchKey={rangeTerminalLaunchKey}
            onClose={closeConsole}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
