"use client";

import type { LucideIcon } from "lucide-react";
import { Boxes, Code2, Cog, Database, FileBarChart, LayoutTemplate, Radar, Server, Signal } from "lucide-react";

import { LandingReveal } from "@/components/landing/landing-reveal";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

type Accent = "cyan" | "violet" | "emerald" | "amber";

type StatDef = {
  id: string;
  value: string;
  label: string;
  hint: string;
  icon: LucideIcon;
  accent: Accent;
  tags?: readonly string[];
  gridClass: string;
};

const stats: readonly StatDef[] = [
  {
    id: "rules",
    value: "5+",
    label: "Detection rule families",
    hint: "Brute force, port scan, rate anomaly, and more — wired into the same pipeline as live telemetry.",
    icon: Radar,
    accent: "cyan",
    tags: ["brute_force_login", "port_scan_recon", "data_exfiltration", "rate_anomaly"],
    gridClass: "lg:col-span-7",
  },
  {
    id: "severity",
    value: "4",
    label: "Severity levels",
    hint: "From low to critical, aligned with triage queues and SLAs.",
    icon: Signal,
    accent: "violet",
    gridClass: "lg:col-span-5",
  },
  {
    id: "reports",
    value: "2",
    label: "Report channels",
    hint: "On-demand PDFs and scheduled digests for leadership-ready summaries.",
    icon: FileBarChart,
    accent: "emerald",
    gridClass: "lg:col-span-5",
  },
  {
    id: "stack",
    value: "Full",
    label: "Modern stack",
    hint: "Composable services you can run locally or ship behind your own gateway.",
    icon: Boxes,
    accent: "amber",
    gridClass: "lg:col-span-7 lg:col-start-6",
  },
] as const;

/** Landing labels → how the engine decides (aligned with `detection/rules`). */
const RULE_DETECTION_INFO: Record<string, { title: string; body: string }> = {
  brute_force_login: {
    title: "Correlated authentication failures",
    body: "We roll up failed or denied login-style events from the same source IP inside a short sliding window (minutes). When the count crosses a threshold, we raise a high-severity alert so brute-force bursts stand out from one-off typos.",
  },
  port_scan_recon: {
    title: "Reconnaissance-style port sweep",
    body: "Distinct destination ports from one host in a tight time window suggest horizontal discovery. The engine counts unique ports per source and fires when recon behavior exceeds normal single-service noise.",
  },
  data_exfiltration: {
    title: "Sensitive egress and volume signals",
    body: "DLP-flavored heuristics watch for large outbound transfers, archives, or transfers tagged as sensitive combined with destination context. Multiple corroborating fields reduce false positives from benign bulk jobs.",
  },
  rate_anomaly: {
    title: "Event-rate spike vs recent baseline",
    body: "We compare ingest velocity to a trailing baseline for the tenant. A sudden flood of events—benign misconfig or attack-driven noise—gets flagged as event-rate anomaly so operators notice infrastructure or campaign shifts early.",
  },
};

type StackTech = {
  label: string;
  mono: string;
  tip: string;
  icon: LucideIcon;
  bar: string;
  iconWrap: string;
};

const STACK_TECH: readonly StackTech[] = [
  {
    label: "FastAPI",
    mono: "async api",
    tip: "Async Python API for auth, scenarios, event ingestion, and OpenAPI-backed contracts your agents and UI share.",
    icon: Code2,
    bar: "from-teal-400/90 to-emerald-600/80",
    iconWrap: "border-teal-500/35 bg-teal-500/10 text-teal-200",
  },
  {
    label: "Next.js",
    mono: "app router",
    tip: "App Router frontend for dashboards, Attack Lab, and reports—server and client components where each fits best.",
    icon: LayoutTemplate,
    bar: "from-zinc-200/90 to-zinc-500/70",
    iconWrap: "border-zinc-400/35 bg-zinc-500/15 text-zinc-100",
  },
  {
    label: "Postgres",
    mono: "oltp + audit",
    tip: "System of record for users, alerts, incidents, audit trails, and reports—relational data with migrations via Alembic.",
    icon: Database,
    bar: "from-sky-400/90 to-blue-700/80",
    iconWrap: "border-sky-500/40 bg-sky-500/10 text-sky-200",
  },
  {
    label: "Redis",
    mono: "broker · cache",
    tip: "Fast cache and Celery broker so background work (digests, broadcasts, heavy tasks) stays off the request path.",
    icon: Server,
    bar: "from-rose-400/90 to-red-700/75",
    iconWrap: "border-rose-500/40 bg-rose-500/10 text-rose-100",
  },
  {
    label: "Celery",
    mono: "workers",
    tip: "Async workers for scheduled reports, PDF generation, and other jobs that should not block the API or browser.",
    icon: Cog,
    bar: "from-lime-300/90 to-green-700/80",
    iconWrap: "border-lime-500/35 bg-lime-500/10 text-lime-100",
  },
] as const;

const tooltipShell =
  "!max-w-[min(22rem,calc(100vw-1.5rem))] !rounded-xl !border !border-cyan-500/35 !bg-zinc-950/98 !p-0 !text-left !shadow-[0_24px_60px_-12px_rgba(0,0,0,0.88)] !backdrop-blur-xl";

const stackTooltipShell =
  "!max-w-[min(20rem,calc(100vw-1.5rem))] !rounded-xl !border !border-amber-500/30 !bg-zinc-950/98 !p-0 !text-left !shadow-[0_24px_60px_-12px_rgba(0,0,0,0.88)] !backdrop-blur-xl";

function RuleTooltipBody({ ruleKey }: { ruleKey: string }) {
  const info = RULE_DETECTION_INFO[ruleKey] ?? {
    title: "Detection rule",
    body: "Rule evaluates normalized security events in the ingestion pipeline and opens alerts when its conditions match your tenant policy.",
  };
  return (
    <div className="overflow-hidden rounded-[inherit]">
      <div className="border-b border-cyan-500/25 bg-gradient-to-r from-cyan-500/15 via-cyan-500/5 to-violet-600/10 px-3 py-2.5">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-300/95">{ruleKey}</p>
        <p className="mt-1 text-sm font-semibold leading-snug text-white">{info.title}</p>
      </div>
      <p className="px-3 py-3 text-[11px] leading-relaxed text-zinc-300">{info.body}</p>
    </div>
  );
}

function StackTooltipBody({ tip }: { tip: string }) {
  return (
    <div className="overflow-hidden rounded-[inherit]">
      <div className="border-b border-amber-500/25 bg-gradient-to-r from-amber-500/15 via-transparent to-violet-600/10 px-3 py-2">
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-200/95">Why this layer</p>
      </div>
      <p className="px-3 py-2.5 text-[11px] leading-relaxed text-zinc-300">{tip}</p>
    </div>
  );
}

const accentRing: Record<Accent, string> = {
  cyan: "ring-cyan-500/25 hover:ring-cyan-400/40",
  violet: "ring-violet-500/25 hover:ring-violet-400/40",
  emerald: "ring-emerald-500/25 hover:ring-emerald-400/40",
  amber: "ring-amber-500/25 hover:ring-amber-400/40",
};

const accentBar: Record<Accent, string> = {
  cyan: "from-cyan-400 to-cyan-600",
  violet: "from-violet-400 to-violet-600",
  emerald: "from-emerald-400 to-emerald-600",
  amber: "from-amber-400 to-amber-600",
};

const accentIcon: Record<Accent, string> = {
  cyan: "text-cyan-300/95",
  violet: "text-violet-300/95",
  emerald: "text-emerald-300/95",
  amber: "text-amber-300/95",
};

const accentGlow: Record<Accent, string> = {
  cyan: "shadow-[0_0_48px_-20px_rgba(34,211,238,0.35)]",
  violet: "shadow-[0_0_48px_-20px_rgba(167,139,250,0.35)]",
  emerald: "shadow-[0_0_48px_-20px_rgba(52,211,153,0.3)]",
  amber: "shadow-[0_0_48px_-20px_rgba(251,191,36,0.28)]",
};

const severitySteps = ["Low", "Med", "High", "Crit"] as const;

function StatCard({ s, index }: { s: StatDef; index: number }) {
  const Icon = s.icon;
  const isStack = s.id === "stack";
  const isSeverity = s.id === "severity";

  return (
    <LandingReveal delay={0.05 * index} className={cn("min-w-0", s.gridClass)}>
      <article
        className={cn(
          "group relative flex h-full min-h-[11rem] w-full min-w-0 flex-col overflow-hidden rounded-[var(--landing-radius-hud)] border border-white/[0.06] bg-zinc-950/55 p-5 shadow-lg shadow-black/40 ring-1 backdrop-blur-md transition-all duration-300",
          accentRing[s.accent],
          "hover:-translate-y-0.5 hover:border-white/10",
          accentGlow[s.accent],
        )}
      >
        <div
          className={cn(
            "pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent to-transparent opacity-80",
            s.accent === "cyan" && "via-cyan-400/50",
            s.accent === "violet" && "via-violet-400/50",
            s.accent === "emerald" && "via-emerald-400/50",
            s.accent === "amber" && "via-amber-400/50",
          )}
          aria-hidden
        />
        <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-gradient-to-br from-white/[0.04] to-transparent blur-2xl" aria-hidden />

        <div className="flex items-start justify-between gap-3">
          <div
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-black/40",
              accentIcon[s.accent],
            )}
          >
            <Icon className="h-5 w-5" aria-hidden />
          </div>
          <p
            className={cn(
              "font-[family-name:var(--font-display)] text-4xl font-bold tabular-nums tracking-tight sm:text-5xl",
              s.accent === "cyan" && "bg-gradient-to-br from-cyan-200 to-cyan-500 bg-clip-text text-transparent",
              s.accent === "violet" && "bg-gradient-to-br from-violet-200 to-violet-500 bg-clip-text text-transparent",
              s.accent === "emerald" &&
                "bg-gradient-to-br from-emerald-200 to-emerald-500 bg-clip-text text-transparent",
              s.accent === "amber" && "bg-gradient-to-br from-amber-200 to-amber-500 bg-clip-text text-transparent",
            )}
          >
            {s.value}
          </p>
        </div>

        <h3 className="mt-4 font-[family-name:var(--font-display)] text-base font-semibold tracking-tight text-foreground">
          {s.label}
        </h3>
        <p className="mt-1.5 flex-1 text-xs leading-relaxed text-muted-foreground sm:text-sm">{s.hint}</p>

        {s.tags && s.tags.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {s.tags.map((tag) => (
              <Tooltip key={tag}>
                <TooltipTrigger
                  render={
                    <button
                      type="button"
                      className={cn(
                        "rounded-lg border border-cyan-500/30 bg-gradient-to-b from-cyan-500/[0.12] to-black/40 px-2.5 py-1.5 font-mono text-[10px] font-medium text-cyan-100/95 shadow-sm shadow-cyan-950/40",
                        "transition-all hover:border-cyan-400/55 hover:shadow-[0_0_20px_-6px_rgba(34,211,238,0.45)]",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60",
                        "cursor-help",
                      )}
                    >
                      {tag}
                    </button>
                  }
                />
                <TooltipContent side="top" align="start" className={tooltipShell}>
                  <RuleTooltipBody ruleKey={tag} />
                </TooltipContent>
              </Tooltip>
            ))}
          </div>
        ) : null}

        {isSeverity ? (
          <div className="mt-4" aria-hidden>
            <div className="mb-1.5 flex justify-between text-[9px] font-medium uppercase tracking-wider text-zinc-500">
              {severitySteps.map((step) => (
                <span key={step}>{step}</span>
              ))}
            </div>
            <div className="flex h-2 gap-1">
              {[
                "bg-emerald-600/75",
                "bg-amber-500/85",
                "bg-rose-500/90",
                "bg-fuchsia-500 shadow-[0_0_14px_rgba(217,70,239,0.45)]",
              ].map((barClass, i) => (
                <span key={severitySteps[i]} className={cn("h-full flex-1 rounded-sm", barClass)} />
              ))}
            </div>
          </div>
        ) : null}

        {isStack ? (
          <div className="relative mt-4 border-t border-white/[0.06] pt-4">
            <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-200/70">
              Production spine · hover each layer
            </p>
            <div className="relative overflow-hidden rounded-xl border border-amber-500/25 bg-gradient-to-b from-zinc-950/90 to-black/80 p-1.5 shadow-inner ring-1 ring-amber-500/10">
              <div
                className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_120%_at_50%_-20%,rgba(251,191,36,0.08),transparent_50%)]"
                aria-hidden
              />
              <div className="relative flex flex-col divide-y divide-white/[0.08] sm:flex-row sm:divide-x sm:divide-y-0 sm:divide-white/[0.08]">
                {STACK_TECH.map((item) => {
                  const TechIcon = item.icon;
                  return (
                    <Tooltip key={item.label}>
                      <TooltipTrigger
                        render={
                          <button
                            type="button"
                            className={cn(
                              "flex min-h-[5.5rem] flex-1 flex-col items-center justify-center gap-2 px-2 py-3 text-center transition-colors",
                              "hover:bg-white/[0.04] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-amber-400/50",
                              "cursor-help sm:px-3",
                            )}
                          >
                            <div
                              className={cn(
                                "flex h-11 w-11 items-center justify-center rounded-xl border bg-black/35 shadow-md",
                                item.iconWrap,
                              )}
                            >
                              <TechIcon className="h-5 w-5" aria-hidden />
                            </div>
                            <span className="font-[family-name:var(--font-display)] text-xs font-semibold text-zinc-100">
                              {item.label}
                            </span>
                            <span className="font-mono text-[9px] uppercase tracking-wider text-zinc-500">{item.mono}</span>
                            <span
                              className={cn(
                                "h-0.5 w-10 rounded-full bg-gradient-to-r opacity-90",
                                item.bar,
                              )}
                              aria-hidden
                            />
                          </button>
                        }
                      />
                      <TooltipContent side="top" className={stackTooltipShell}>
                        <StackTooltipBody tip={item.tip} />
                      </TooltipContent>
                    </Tooltip>
                  );
                })}
              </div>
            </div>
          </div>
        ) : null}

        <div
          className={cn(
            "pointer-events-none absolute bottom-0 left-4 right-4 h-0.5 rounded-full bg-gradient-to-r opacity-60 transition-opacity group-hover:opacity-100",
            accentBar[s.accent],
          )}
          aria-hidden
        />
      </article>
    </LandingReveal>
  );
}

export function LandingStats() {
  return (
    <section
      id="prototype"
      className="landing-section relative z-10 scroll-mt-24 overflow-hidden border-y border-white/[0.07]"
    >
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_90%_60%_at_10%_20%,oklch(0.28_0.08_260)_0%,transparent_55%),radial-gradient(ellipse_70%_50%_at_90%_80%,oklch(0.22_0.06_200)_0%,transparent_50%)]"
        aria-hidden
      />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,oklch(0.12_0.02_260)_0%,transparent_35%,oklch(0.1_0.02_260)_100%)]" aria-hidden />

      <div className="relative mx-auto max-w-[var(--landing-max)] px-6 py-14 lg:px-8 lg:py-20">
        <LandingReveal>
          <div className="mx-auto mb-12 max-w-3xl text-center lg:mb-14">
            <p className="landing-eyebrow mb-4 text-muted-foreground">Why teams prototype on CyberGuard</p>
            <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-[-0.03em] text-foreground sm:text-4xl lg:text-[2.35rem] lg:leading-[1.12]">
              Ship detection-grade demos{" "}
              <span className="bg-gradient-to-r from-cyan-300 via-violet-300 to-cyan-200 bg-clip-text text-transparent">
                without wiring a SOC from scratch
              </span>
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">
              Rule bundles, severities, and reporting paths behave like production — so stakeholders see believable
              alerts, not toy dashboards.
            </p>
          </div>
        </LandingReveal>

        <div className="grid auto-rows-fr gap-4 sm:grid-cols-2 lg:grid-cols-12 lg:gap-5">
          {stats.map((s, i) => (
            <StatCard key={s.id} s={s} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
