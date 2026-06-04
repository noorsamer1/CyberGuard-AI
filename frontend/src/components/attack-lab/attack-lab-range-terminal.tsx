"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useCallback, useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

const LINE_DELAY_MS = 260;

export interface RangeRunResultLike {
  message: string;
  requests_executed: number;
  logs_collected: number;
  events_ingested: number;
  alerts_generated: number;
  incidents_created: number;
  executed_commands?: string[];
}

type RangeTerminalContextInput = {
  scenarioId: string | null;
  scenarioName: string;
  targetUrl: string;
  executionCommands: string[];
};

function buildManualCollectScript(targetUrl: string): string[] {
  return [
    "$ cyberguard range collect --drain",
    `curl -s ${targetUrl.replace(/\/+$/, "")}/_range/logs -H "X-Range-Secret: ***"`,
    "→ parse log frames → normalize → ingest_batch()",
  ];
}

function buildScriptLines(ctx: RangeTerminalContextInput): string[] {
  const { scenarioId, scenarioName, targetUrl, executionCommands } = ctx;

  if (scenarioId === "manual_collect") {
    return buildManualCollectScript(targetUrl);
  }

  if (executionCommands.length > 0) {
    return [
      `$ cyberguard range run ${scenarioId ?? "scenario"} -- ${scenarioName}`,
      "→ reset target state, execute attack sequence, drain logs",
      ...executionCommands,
      "→ correlation engine + detection rules",
    ];
  }

  return [
    `$ cyberguard range run ${scenarioId ?? "scenario"}`,
    `→ ${scenarioName}`,
    "→ waiting for execution script from API…",
  ];
}

function buildResultLines(r: RangeRunResultLike): string[] {
  return [
    `[ok] ${r.message}`,
    `requests_executed=${r.requests_executed}`,
    `logs_collected=${r.logs_collected}`,
    `events_ingested=${r.events_ingested}`,
    `alerts_generated=${r.alerts_generated}`,
    `incidents_created=${r.incidents_created}`,
  ];
}

export type AttackLabRangeTerminalProps = {
  launchKey: number;
  scenarioId: string | null;
  scenarioName: string;
  targetUrl: string;
  /** Exact curl/probe lines (reset → attacks → drain) from GET /range/scenarios or run result. */
  executionCommands: string[];
  isBusy: boolean;
  result: RangeRunResultLike | null;
};

/**
 * Timed terminal replay of the real range runner commands (parallel to live API).
 */
export function AttackLabRangeTerminal({
  launchKey,
  scenarioId,
  scenarioName,
  targetUrl,
  executionCommands,
  isBusy,
  result,
}: AttackLabRangeTerminalProps) {
  const reducedMotion = useReducedMotion();
  const [scriptVisible, setScriptVisible] = useState(0);
  const [scriptDone, setScriptDone] = useState(false);
  const [resultVisible, setResultVisible] = useState(0);
  const scriptTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const resultTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearScriptTimers = useCallback(() => {
    scriptTimersRef.current.forEach((t) => clearTimeout(t));
    scriptTimersRef.current = [];
  }, []);

  const clearResultTimers = useCallback(() => {
    resultTimersRef.current.forEach((t) => clearTimeout(t));
    resultTimersRef.current = [];
  }, []);

  useEffect(() => {
    clearScriptTimers();
    clearResultTimers();
    setScriptVisible(0);
    setResultVisible(0);
    setScriptDone(false);

    const lines = buildScriptLines({
      scenarioId,
      scenarioName,
      targetUrl,
      executionCommands,
    });

    if (reducedMotion) {
      setScriptVisible(lines.length);
      setScriptDone(true);
      return;
    }

    lines.forEach((_, i) => {
      const t = setTimeout(() => setScriptVisible(i + 1), (i + 1) * LINE_DELAY_MS);
      scriptTimersRef.current.push(t);
    });
    const doneT = setTimeout(() => setScriptDone(true), lines.length * LINE_DELAY_MS + 120);
    scriptTimersRef.current.push(doneT);

    return () => {
      clearScriptTimers();
    };
  }, [
    launchKey,
    scenarioId,
    scenarioName,
    targetUrl,
    executionCommands,
    reducedMotion,
    clearScriptTimers,
    clearResultTimers,
  ]);

  useEffect(() => {
    if (!scriptDone) {
      return;
    }
    clearResultTimers();
    setResultVisible(0);

    if (!result) {
      return;
    }

    const lines = buildResultLines(result);
    if (reducedMotion) {
      setResultVisible(lines.length);
      return;
    }

    lines.forEach((_, i) => {
      const t = setTimeout(() => setResultVisible(i + 1), (i + 1) * LINE_DELAY_MS);
      resultTimersRef.current.push(t);
    });

    return () => clearResultTimers();
  }, [scriptDone, result, reducedMotion, clearResultTimers]);

  const scriptLines = buildScriptLines({
    scenarioId,
    scenarioName,
    targetUrl,
    executionCommands,
  });
  const visibleScript = scriptLines.slice(0, scriptVisible);
  const resultLines = result ? buildResultLines(result) : [];
  const visibleResult = resultLines.slice(0, resultVisible);

  const scriptTyping =
    !reducedMotion && !scriptDone && scriptVisible < scriptLines.length;

  return (
    <div
      className="rounded-md border border-cyan-500/20 bg-black/50 p-4 font-mono text-[11px] leading-relaxed text-cyan-100/95 sm:text-xs"
      aria-live="polite"
      aria-atomic="false"
    >
      <div className="mb-2 flex items-center justify-between gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        <span>Range runner</span>
        <span
          className={cn(
            "rounded-full border border-emerald-500/35 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-100",
            (isBusy || scriptTyping) && "animate-pulse",
          )}
        >
          {!scriptDone ? "RUN…" : isBusy && !result ? "API…" : result ? "DONE" : "WAIT"}
        </span>
      </div>
      {visibleScript.map((line, idx) => (
        <motion.p
          key={`s-${launchKey}-${idx}-${line.slice(0, 32)}`}
          initial={reducedMotion ? false : { opacity: 0, x: -6 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: reducedMotion ? 0 : 0.18 }}
          className={cn(
            line.startsWith("$") && "text-cyan-300",
            line.startsWith("curl") && "break-all text-emerald-100/90",
            line.startsWith("python3") && "break-all text-emerald-100/90",
            line.startsWith("→") && "text-cyan-100/55",
          )}
        >
          {line}
        </motion.p>
      ))}
      {scriptTyping ? (
        <span className="mt-1 inline-block h-3 w-2 animate-pulse bg-cyan-400/80 align-middle" aria-hidden />
      ) : null}

      {scriptDone && visibleResult.length > 0 ? (
        <div className="mt-4 border-t border-white/10 pt-3">
          {visibleResult.map((line, idx) => (
            <motion.p
              key={`r-${launchKey}-${idx}-${line.slice(0, 20)}`}
              initial={reducedMotion ? false : { opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: reducedMotion ? 0 : 0.18 }}
              className={cn(line.startsWith("[ok]") ? "text-green-400" : "text-muted-foreground")}
            >
              {line}
            </motion.p>
          ))}
          {!reducedMotion && result && resultVisible < resultLines.length ? (
            <span className="mt-1 inline-block h-3 w-2 animate-pulse bg-emerald-400/80 align-middle" aria-hidden />
          ) : null}
        </div>
      ) : null}

      {scriptDone && !result && isBusy ? (
        <p className="mt-4 border-t border-white/10 pt-3 text-muted-foreground animate-pulse">
          … waiting for backend (attack script finished; ingesting logs)
        </p>
      ) : null}

      {scriptDone && !result && !isBusy ? (
        <p className="mt-4 border-t border-white/10 pt-3 text-rose-300/90">
          No result payload (request may have failed — see toast).
        </p>
      ) : null}
    </div>
  );
}
