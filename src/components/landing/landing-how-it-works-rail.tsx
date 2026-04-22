"use client";

import { LandingReveal } from "@/components/landing/landing-reveal";
import { cn } from "@/lib/utils";

const steps = [
  {
    kicker: "01 · Ingest",
    title: "Normalize hostile-shaped telemetry",
    detail:
      "Batch REST ingest, CSV/line uploads, and Attack Lab bundles land in the same schema: IPs, users, ports, MITRE hints, and severity hints preserved for downstream rules.",
    metric: "50+ structured fields",
    accent: "from-cyan-500/30 to-cyan-500/5",
    ring: "ring-cyan-500/25",
  },
  {
    kicker: "02 · Detect",
    title: "Rule engine with explainable thresholds",
    detail:
      "Brute-force rollups, port-sweep counters, DLP-flavored exfiltration heuristics, and rate anomalies evaluate per-tenant windows — every firing maps to a named rule family you can open in code review.",
    metric: "5+ rule families",
    accent: "from-violet-500/30 to-violet-500/5",
    ring: "ring-violet-500/25",
  },
  {
    kicker: "03 · Alert & fan-out",
    title: "Sub-second operator visibility",
    detail:
      "WebSocket channels push alert lifecycle transitions to the console while Celery-friendly workers stay off the request path for heavier jobs.",
    metric: "Live WS channel",
    accent: "from-amber-500/25 to-amber-500/5",
    ring: "ring-amber-500/25",
  },
  {
    kicker: "04 · Incident",
    title: "Automatic escalation with human gates",
    detail:
      "High and critical severities open incidents with owner isolation, preserving MTTA/MTTR math for dashboards and PDF timelines.",
    metric: "4 severities",
    accent: "from-rose-500/25 to-rose-500/5",
    ring: "ring-rose-500/25",
  },
  {
    kicker: "05 · Narrate",
    title: "Optional AI + always-on exports",
    detail:
      "OpenRouter-backed structured briefings augment incidents; PDFs and SMTP digests close the loop for leadership-ready storytelling.",
    metric: "PDF + digest",
    accent: "from-emerald-500/25 to-emerald-500/5",
    ring: "ring-emerald-500/25",
  },
];

export function LandingHowItWorksRail() {
  return (
    <section id="how-it-works" className="landing-section relative z-10 scroll-mt-24" aria-labelledby="how-heading">
      <div className="mx-auto max-w-[var(--landing-max)] px-6 lg:px-8">
        <LandingReveal mode="deep">
          <p className="landing-eyebrow text-cyan-300/90">How it works</p>
          <h2
            id="how-heading"
            className="mt-2 max-w-3xl font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight text-foreground sm:text-4xl lg:text-[2.35rem] lg:leading-tight"
          >
            Five engineering stages, one continuous spine
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground sm:text-base">
            Five deployable slices in this repo — each card is a real module boundary (ingest workers, rules engine,
            WebSocket fan-out, incidents, reporting). No scroll tricks: scan the grid like an architecture wall.
          </p>
        </LandingReveal>

        <div className="relative mt-12 lg:mt-14">
          <div
            className="pointer-events-none absolute -inset-x-4 -top-8 bottom-0 -z-10 rounded-[2.5rem] bg-[radial-gradient(ellipse_80%_60%_at_50%_40%,oklch(0.35_0.12_250_/_0.14),transparent_65%)] opacity-90 blur-2xl sm:-inset-x-8"
            aria-hidden
          />

          <ul className="grid list-none grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3 xl:gap-7">
            {steps.map((s, index) => (
              <li
                key={s.kicker}
                className={cn(
                  "group relative",
                  index % 2 === 0 ? "xl:-translate-y-2" : "xl:translate-y-3",
                )}
              >
                <article
                  className={cn(
                    "flex h-full flex-col justify-between rounded-2xl border border-border/50 bg-card/60 p-6 shadow-[0_20px_50px_-24px_rgba(0,0,0,0.65)] ring-1 ring-inset ring-white/[0.06] backdrop-blur-md transition-[transform,box-shadow,border-color] duration-300 ease-out",
                    "hover:-translate-y-2 hover:border-cyan-500/25 hover:shadow-[0_28px_70px_-28px_rgba(0,0,0,0.75),0_0_0_1px_oklch(0.72_0.14_230_/_0.12)]",
                    "motion-reduce:transform-none motion-reduce:hover:transform-none",
                    s.ring,
                  )}
                >
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                      {s.kicker}
                    </p>
                    <h3 className="mt-3 font-[family-name:var(--font-display)] text-lg font-semibold tracking-tight text-foreground sm:text-xl">
                      {s.title}
                    </h3>
                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{s.detail}</p>
                  </div>
                  <div
                    className={cn(
                      "mt-6 inline-flex w-fit items-center rounded-full border border-white/10 bg-gradient-to-r px-3 py-1 text-[11px] font-semibold text-foreground",
                      s.accent,
                    )}
                  >
                    {s.metric}
                  </div>
                </article>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
