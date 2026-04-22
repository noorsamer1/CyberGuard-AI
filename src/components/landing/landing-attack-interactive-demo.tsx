"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Activity, Copy, RotateCcw, Zap } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { useLandingScroll } from "@/components/landing/landing-scroll-context";
import { Button } from "@/components/ui/button";
import { API_BASE } from "@/lib/constants";
import { cn } from "@/lib/utils";

/** Mirrors backend `scenario_service.SCENARIOS` (subset) for labels + in-browser preview script. */
export type DemoScenario = {
  id: string;
  name: string;
  severity: "medium" | "high" | "critical";
  mitreTechniques: readonly string[];
  terminalLines: readonly string[];
  alerts: readonly { title: string; rule: string; severity: "medium" | "high" | "critical" }[];
};

/** CLI-style command shown on the landing demo (mirrors first terminal line). */
export function launchCliCommand(scenarioId: string): string {
  return `cyberguard scenario run ${scenarioId}`;
}

/** Example HTTP call (requires a bearer token from sign-in). */
export function launchCurlCommand(scenarioId: string): string {
  return [
    `curl -sS -X POST "${API_BASE}/api/v1/scenarios/${scenarioId}/run" \\`,
    `  -H "Authorization: Bearer $TOKEN" \\`,
    `  -H "Content-Type: application/json" \\`,
    `  -d '{}'`,
  ].join("\n");
}

export const LANDING_DEMO_SCENARIOS: readonly DemoScenario[] = [
  {
    id: "ssh_brute_force",
    name: "SSH Brute Force",
    severity: "high",
    mitreTechniques: ["T1110.003"],
    terminalLines: [
      `$ ${launchCliCommand("ssh_brute_force")}`,
      `→ POST ${API_BASE}/api/v1/scenarios/ssh_brute_force/run`,
      "→ ingest_batch(847 events) · owner scoped",
      "→ rule: brute_force_login · severity: high",
      "→ incident opened · assignee queue: default",
    ],
    alerts: [{ title: "Burst SSH auth failures", rule: "brute_force_login", severity: "high" }],
  },
  {
    id: "port_scan_exploit",
    name: "Port scan & exploit",
    severity: "high",
    mitreTechniques: ["T1046", "T1190"],
    terminalLines: [
      `$ ${launchCliCommand("port_scan_exploit")}`,
      `→ POST ${API_BASE}/api/v1/scenarios/port_scan_exploit/run`,
      "→ correlation: recon sweep → web exploit attempts",
      "→ rules: port_scan_recon, suspicious_outbound",
    ],
    alerts: [
      { title: "Horizontal port sweep", rule: "port_scan_recon", severity: "high" },
      { title: "Web shell staging", rule: "suspicious_outbound", severity: "medium" },
    ],
  },
  {
    id: "data_exfiltration",
    name: "Insider exfiltration",
    severity: "high",
    mitreTechniques: ["T1560", "T1048"],
    terminalLines: [
      `$ ${launchCliCommand("data_exfiltration")}`,
      `→ POST ${API_BASE}/api/v1/scenarios/data_exfiltration/run`,
      "→ DLP: sensitive archive + HTTPS egress spike",
      "→ rule: data_exfiltration · playbook: insider-threat-01",
    ],
    alerts: [{ title: "Sensitive data egress", rule: "data_exfiltration", severity: "high" }],
  },
  {
    id: "ransomware_chain",
    name: "Ransomware chain",
    severity: "critical",
    mitreTechniques: ["T1046", "T1021.001", "T1486"],
    terminalLines: [
      `$ ${launchCliCommand("ransomware_chain")}`,
      `→ POST ${API_BASE}/api/v1/scenarios/ransomware_chain/run`,
      "→ kill chain: scan → lateral SMB → encryption payload",
      "→ 2 correlated incidents · executive briefing suggested",
    ],
    alerts: [
      { title: "Mass file tamper", rule: "ransomware_precursor", severity: "critical" },
      { title: "SMB lateral spread", rule: "lateral_movement_smb", severity: "high" },
    ],
  },
] as const;

type Phase = "idle" | "running" | "complete";

const severityClass: Record<DemoScenario["severity"], string> = {
  medium: "border-amber-500/40 bg-amber-500/15 text-amber-200",
  high: "border-rose-500/40 bg-rose-500/15 text-rose-200",
  critical: "border-fuchsia-500/50 bg-fuchsia-500/20 text-fuchsia-100",
};

export function LandingAttackInteractiveDemo() {
  const scrollCtx = useLandingScroll();
  const reducedMotion = scrollCtx?.reducedMotion ?? false;

  const [selectedId, setSelectedId] = useState<string>(LANDING_DEMO_SCENARIOS[0]!.id);
  const [phase, setPhase] = useState<Phase>("idle");
  const [lineCount, setLineCount] = useState(0);
  const [alertCount, setAlertCount] = useState(0);
  const [copiedKind, setCopiedKind] = useState<null | "cli" | "curl">(null);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const copyResetRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const copyLaunchText = useCallback(async (text: string, kind: "cli" | "curl") => {
    try {
      await navigator.clipboard.writeText(text);
      if (copyResetRef.current) clearTimeout(copyResetRef.current);
      setCopiedKind(kind);
      copyResetRef.current = setTimeout(() => {
        setCopiedKind(null);
        copyResetRef.current = null;
      }, 2000);
    } catch {
      setCopiedKind(null);
    }
  }, []);

  useEffect(
    () => () => {
      if (copyResetRef.current) clearTimeout(copyResetRef.current);
    },
    [],
  );

  const scenario =
    LANDING_DEMO_SCENARIOS.find((s) => s.id === selectedId) ?? LANDING_DEMO_SCENARIOS[0]!;

  const clearTimers = useCallback(() => {
    timersRef.current.forEach((t) => clearTimeout(t));
    timersRef.current = [];
  }, []);

  useEffect(() => () => clearTimers(), [clearTimers]);

  const resetDemo = useCallback(() => {
    clearTimers();
    setPhase("idle");
    setLineCount(0);
    setAlertCount(0);
  }, [clearTimers]);

  const runDemo = useCallback(() => {
    clearTimers();
    setPhase("running");
    setLineCount(0);
    setAlertCount(0);

    const scen =
      LANDING_DEMO_SCENARIOS.find((s) => s.id === selectedId) ?? LANDING_DEMO_SCENARIOS[0]!;
    const lines = scen.terminalLines;
    const alerts = scen.alerts;

    if (reducedMotion) {
      setLineCount(lines.length);
      setAlertCount(alerts.length);
      setPhase("complete");
      return;
    }

    const lineDelay = 380;
    lines.forEach((_, i) => {
      const t = setTimeout(() => setLineCount(i + 1), (i + 1) * lineDelay);
      timersRef.current.push(t);
    });

    const alertsStart = lines.length * lineDelay + 420;
    alerts.forEach((_, i) => {
      const t = setTimeout(() => setAlertCount(i + 1), alertsStart + i * 320);
      timersRef.current.push(t);
    });

    const done = setTimeout(() => {
      setPhase("complete");
    }, alertsStart + alerts.length * 320 + 400);
    timersRef.current.push(done);
  }, [clearTimers, reducedMotion, selectedId]);

  const onSelectScenario = (id: string) => {
    setSelectedId(id);
    resetDemo();
  };

  const terminalLines = scenario.terminalLines.slice(
    0,
    reducedMotion && phase === "complete" ? scenario.terminalLines.length : lineCount,
  );

  const statusLabel = phase === "idle" ? "READY" : phase === "running" ? "RUN…" : "DONE";

  return (
    <div className="landing-hud-card space-y-4 rounded-[var(--landing-radius-hud)] border border-cyan-500/40 bg-gradient-to-b from-zinc-950/90 to-black/70 p-4 shadow-[0_0_40px_-12px_rgba(34,211,238,0.25)] ring-1 ring-cyan-500/15 backdrop-blur-xl sm:p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2 font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-cyan-200/95">
          <span className="text-cyan-400/90" aria-hidden>
            &gt;_
          </span>
          Interactive scenario
        </div>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "flex items-center gap-1.5 rounded-full border border-emerald-500/35 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-100",
              phase === "running" && "animate-pulse",
            )}
          >
            <span className="relative flex h-2 w-2">
              {phase === "running" ? (
                <>
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-40" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
                </>
              ) : (
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
              )}
            </span>
            {statusLabel}
          </span>
        </div>
      </div>

      <p id="demo-scenario-label" className="text-[11px] leading-relaxed text-muted-foreground">
        Browser-only preview — no account, no network call. Lines show the same paths your API would use (
        <span className="font-mono text-[10px] text-cyan-200/80">{API_BASE}</span>
        ). Open <strong className="text-foreground/90">Attack Lab</strong> in the product when you want real runs.
      </p>

      <div
        className="flex flex-wrap gap-2"
        role="listbox"
        aria-labelledby="demo-scenario-label"
        aria-activedescendant={`scenario-${selectedId}`}
      >
        {LANDING_DEMO_SCENARIOS.map((s) => {
          const active = s.id === selectedId;
          return (
            <button
              key={s.id}
              type="button"
              id={`scenario-${s.id}`}
              role="option"
              aria-selected={active}
              onClick={() => onSelectScenario(s.id)}
              className={cn(
                "rounded-lg border px-3 py-2 text-left text-xs font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/60",
                active
                  ? "border-cyan-400/70 bg-cyan-500/15 text-cyan-50 shadow-[0_0_20px_-8px_rgba(34,211,238,0.45)]"
                  : "border-border/50 bg-background/40 text-muted-foreground hover:border-cyan-500/40 hover:text-foreground",
              )}
            >
              {s.name}
            </button>
          );
        })}
      </div>

      <div className="space-y-3 rounded-lg border border-zinc-700/50 bg-zinc-950/60 p-3 ring-1 ring-white/[0.04]">
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Example launch commands
        </p>
        <p className="text-[10px] leading-relaxed text-zinc-500">
          Same <span className="font-mono text-zinc-400">scenario_id</span> as the API path. Real runs need sign-in
          (bearer token for curl).
        </p>
        <div className="space-y-3">
          <div>
            <div className="mb-1 flex items-center justify-between gap-2">
              <span className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">CLI</span>
              <button
                type="button"
                onClick={() => copyLaunchText(launchCliCommand(selectedId), "cli")}
                className="inline-flex items-center gap-1 rounded-md border border-zinc-700/80 bg-black/40 px-2 py-1 text-[10px] font-medium text-cyan-200/90 transition-colors hover:border-cyan-500/50 hover:bg-cyan-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/60"
              >
                <Copy className="h-3 w-3" aria-hidden />
                {copiedKind === "cli" ? "Copied" : "Copy"}
              </button>
            </div>
            <pre
              className="overflow-x-auto rounded border border-zinc-800/80 bg-black/50 px-2.5 py-2 font-mono text-[10px] leading-relaxed text-cyan-100/95 sm:text-[11px]"
              tabIndex={0}
            >{`$ ${launchCliCommand(selectedId)}`}</pre>
          </div>
          <div>
            <div className="mb-1 flex items-center justify-between gap-2">
              <span className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">curl</span>
              <button
                type="button"
                onClick={() => copyLaunchText(launchCurlCommand(selectedId), "curl")}
                className="inline-flex items-center gap-1 rounded-md border border-zinc-700/80 bg-black/40 px-2 py-1 text-[10px] font-medium text-cyan-200/90 transition-colors hover:border-cyan-500/50 hover:bg-cyan-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/60"
              >
                <Copy className="h-3 w-3" aria-hidden />
                {copiedKind === "curl" ? "Copied" : "Copy"}
              </button>
            </div>
            <pre
              className="max-h-32 overflow-y-auto whitespace-pre-wrap break-all rounded border border-zinc-800/80 bg-black/50 px-2.5 py-2 font-mono text-[9px] leading-relaxed text-cyan-100/90 sm:text-[10px]"
              tabIndex={0}
            >
              {launchCurlCommand(selectedId)}
            </pre>
          </div>
        </div>
        <details className="rounded-md border border-zinc-800/60 bg-black/30 px-2 py-1.5">
          <summary className="cursor-pointer select-none text-[11px] font-medium text-cyan-400/95 hover:text-cyan-300">
            All attacks — CLI one-liners
          </summary>
          <ul className="mt-2 space-y-2 border-t border-zinc-800/60 pt-2 font-mono text-[10px] leading-snug text-zinc-300">
            {LANDING_DEMO_SCENARIOS.map((s) => (
              <li key={s.id}>
                <span className="text-zinc-500">{s.name}</span>
                <span className="mx-1.5 text-zinc-600">·</span>
                <span className="text-cyan-100/90">{launchCliCommand(s.id)}</span>
              </li>
            ))}
          </ul>
        </details>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          onClick={runDemo}
          disabled={phase === "running"}
          className="bg-gradient-to-r from-violet-600 to-cyan-600 text-primary-foreground shadow-md shadow-violet-500/20 hover:from-violet-500 hover:to-cyan-500"
        >
          <Zap className="mr-1.5 h-3.5 w-3.5" aria-hidden />
          Run attack
        </Button>
        <Button type="button" size="sm" variant="outline" onClick={resetDemo} className="border-border/60">
          <RotateCcw className="mr-1.5 h-3.5 w-3.5" aria-hidden />
          Reset
        </Button>
      </div>

      <div
        className="rounded-lg border border-zinc-700/80 bg-zinc-950/95 p-3 font-mono text-[11px] leading-relaxed text-cyan-100/95 shadow-inner sm:text-xs"
        aria-live="polite"
        aria-atomic="false"
      >
        {terminalLines.map((line, idx) => (
          <motion.p
            key={`${line}-${idx}`}
            initial={reducedMotion ? false : { opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: reducedMotion ? 0 : 0.18 }}
            className={cn(line.startsWith("  {") && "text-zinc-300")}
          >
            {line}
          </motion.p>
        ))}
        {phase === "running" && lineCount < scenario.terminalLines.length && !reducedMotion ? (
          <span className="inline-block h-3 w-2 animate-pulse bg-cyan-400/80 align-middle" aria-hidden />
        ) : null}
      </div>

      <div className="border-t border-white/10 pt-3">
        <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          <Activity className="h-3 w-3 text-cyan-400/80" aria-hidden />
          Detection feed (preview)
        </div>
        <ul className="space-y-2">
          <AnimatePresence mode="popLayout">
            {scenario.alerts.slice(0, alertCount).map((a, i) => (
              <motion.li
                key={`${a.title}-${i}`}
                layout
                initial={reducedMotion ? false : { opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: reducedMotion ? 0 : 0.25 }}
                className="flex items-center justify-between gap-2 rounded-md border border-border/50 bg-black/40 px-3 py-2 ring-1 ring-white/5"
              >
                <div>
                  <p className="text-xs font-medium text-foreground">{a.title}</p>
                  <p className="font-mono text-[10px] text-muted-foreground">{a.rule}</p>
                </div>
                <span
                  className={cn(
                    "shrink-0 rounded border px-2 py-0.5 text-[10px] font-semibold uppercase",
                    severityClass[a.severity],
                  )}
                >
                  {a.severity}
                </span>
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
      </div>

      <div className="flex flex-wrap gap-2 border-t border-white/10 pt-3">
        {scenario.mitreTechniques.map((chip) => (
          <span
            key={chip}
            className="rounded border border-cyan-500/40 bg-cyan-500/10 px-2 py-0.5 font-mono text-[10px] text-cyan-100"
          >
            {chip}
          </span>
        ))}
      </div>
    </div>
  );
}
