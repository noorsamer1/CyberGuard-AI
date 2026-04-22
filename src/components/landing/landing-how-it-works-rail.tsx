"use client";

import { LandingReveal } from "@/components/landing/landing-reveal";
import { useLandingScroll } from "@/components/landing/landing-scroll-context";
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

function StaticPipeline() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {steps.map((s) => (
        <article
          key={s.kicker}
          className={cn(
            "rounded-2xl border border-border/50 bg-card/40 p-6 ring-1 ring-white/5 backdrop-blur-md",
            s.ring,
          )}
        >
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">{s.kicker}</p>
          <h3 className="mt-2 font-[family-name:var(--font-display)] text-lg font-semibold text-foreground">{s.title}</h3>
          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{s.detail}</p>
          <p className="mt-4 text-xs font-semibold text-cyan-200/90">{s.metric}</p>
        </article>
      ))}
    </div>
  );
}

export function LandingHowItWorksRail() {
  const reduced = useLandingScroll()?.reducedMotion ?? false;

  if (reduced) {
    return (
      <section id="how-it-works" className="landing-section relative z-10 scroll-mt-24">
        <div className="mx-auto max-w-[var(--landing-max)] px-6 lg:px-8">
          <LandingReveal mode="deep">
            <p className="landing-eyebrow text-cyan-300/90">How it works</p>
            <h2
              id="how-heading"
              className="mt-3 max-w-3xl font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight text-foreground sm:text-4xl"
            >
              Five engineering stages, one continuous spine
            </h2>
            <p className="mt-4 max-w-2xl text-sm text-muted-foreground sm:text-base">
              Reduced motion is on — the horizontal track is shown as a stacked grid instead.
            </p>
          </LandingReveal>
          <div className="mt-10">
            <StaticPipeline />
          </div>
        </div>
      </section>
    );
  }

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
            Scroll the track below to walk the pipeline in order. Each card mirrors a deployable slice of this repo
            (ingest workers, rules, WebSocket fan-out, incidents, reporting). Full-page smooth scroll (Lenis) is paused
            inside the track so horizontal gestures and shift+wheel work reliably.
          </p>
        </LandingReveal>

        <div className="relative mt-10">
          <div
            className="pointer-events-none absolute inset-y-0 left-0 z-[1] w-12 bg-gradient-to-r from-background via-background/85 to-transparent sm:w-16"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute inset-y-0 right-0 z-[1] w-12 bg-gradient-to-l from-background via-background/85 to-transparent sm:w-16"
            aria-hidden
          />

          <div
            data-lenis-prevent
            tabIndex={0}
            role="list"
            aria-label="Analyst pipeline stages — scroll horizontally"
            className={cn(
              "flex snap-x snap-mandatory gap-5 overflow-x-auto overflow-y-hidden pb-4 pt-1",
              "scroll-smooth [-webkit-overflow-scrolling:touch]",
              "outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background",
              "[scrollbar-width:thin] [scrollbar-color:oklch(0.72_0.14_230_/_0.45)_transparent]",
            )}
          >
            {steps.map((s) => (
              <article
                key={s.kicker}
                role="listitem"
                className={cn(
                  "snap-center snap-always flex w-[min(88vw,22.5rem)] shrink-0 flex-col justify-between rounded-2xl border border-border/50 bg-card/55 p-6 shadow-inner shadow-black/25 ring-1 backdrop-blur-md sm:w-[min(72vw,24rem)] sm:p-7",
                  s.ring,
                )}
              >
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                    {s.kicker}
                  </p>
                  <h3 className="mt-3 font-[family-name:var(--font-display)] text-xl font-semibold tracking-tight text-foreground">
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
            ))}
          </div>

          <p className="mt-3 text-center text-xs text-muted-foreground">
            Drag the cards, use a trackpad swipe, or hold <kbd className="rounded border border-border/60 bg-muted/50 px-1.5 py-0.5 font-mono text-[10px]">Shift</kbd>{" "}
            + mouse wheel to scroll sideways.
          </p>
        </div>
      </div>
    </section>
  );
}
