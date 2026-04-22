"use client";

import Link from "next/link";

import { LandingReveal } from "@/components/landing/landing-reveal";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const pipeline = [
  { t: "Ingest", s: "API · CSV · synthetic", c: "bg-cyan-500/20 text-cyan-200", ring: "ring-cyan-500/30" },
  { t: "Detect", s: "Rules + thresholds", c: "bg-violet-500/20 text-violet-200", ring: "ring-violet-500/30" },
  { t: "Alert", s: "WebSocket broadcast", c: "bg-amber-500/15 text-amber-200", ring: "ring-amber-500/25" },
  { t: "Incident", s: "High / critical escalation", c: "bg-rose-500/15 text-rose-200", ring: "ring-rose-500/25" },
  { t: "Report", s: "PDF + scheduled digest", c: "bg-emerald-500/15 text-emerald-200", ring: "ring-emerald-500/25" },
];

export function LandingMission() {
  return (
    <section className="landing-section relative z-10">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-500/35 to-transparent" aria-hidden />
      <div className="mx-auto max-w-[var(--landing-max)] px-6 lg:px-8">
        <div className="grid gap-16 lg:grid-cols-2 lg:items-start lg:gap-24">
          <LandingReveal mode="cinema">
            <p className="landing-eyebrow mb-3 text-cyan-400/90">Mission</p>
            <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-[-0.03em] text-foreground sm:text-4xl lg:text-[2.45rem] lg:leading-[1.12]">
              Close the gap between lecture slides and a believable SOC
            </h2>
            <p className="mt-6 text-base leading-relaxed text-muted-foreground sm:text-lg">
              CyberGuard exists because most training stacks stop at mocked JSON. Here, events traverse the same
              ingestion queue, rule engine, WebSocket fan-out, incident model, and reporting path you would expect in a
              junior SOC rotation — only bounded for classroom safety and disclosure honesty.
            </p>
            <p className="mt-5 text-base leading-relaxed text-muted-foreground sm:text-lg">
              Optional OpenRouter models generate structured analyst briefings, but they never replace the underlying
              evidence objects: alerts retain MITRE mappings, timestamps, and owner scopes so rubrics stay defensible.
            </p>
            <ul className="mt-8 space-y-3 text-sm text-muted-foreground">
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400" aria-hidden />
                <span>
                  <strong className="text-foreground">Owner isolation</strong> keeps cohort tenants from leaking queues
                  while still letting instructors impersonate for grading.
                </span>
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" aria-hidden />
                <span>
                  <strong className="text-foreground">Exports you can defend</strong> — PDFs bundle charts, tables,
                  and optional AI prose for capstone review boards.
                </span>
              </li>
            </ul>
            <Link
              href="/signup"
              className={cn(
                buttonVariants({ variant: "outline" }),
                "mt-10 cursor-pointer border-cyan-500/45 bg-cyan-500/[0.07] text-foreground shadow-[var(--landing-depth-1)] hover:bg-cyan-500/12",
              )}
            >
              Explore the console
            </Link>
          </LandingReveal>

          <LandingReveal mode="deep" delay={0.1}>
            <div className="relative mx-auto w-full max-w-md lg:mx-0 lg:max-w-none">
              <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                    Analyst journey
                  </p>
                  <p className="mt-1 font-[family-name:var(--font-display)] text-lg font-semibold text-foreground">
                    From raw signal to shareable story
                  </p>
                </div>
                <span className="rounded-lg border border-border/55 bg-background/60 px-2.5 py-1 font-mono text-[10px] text-muted-foreground">
                  demo-grade fidelity
                </span>
              </div>

              <div className="relative overflow-hidden rounded-3xl border border-border/50 bg-gradient-to-b from-card/60 via-background/40 to-zinc-950/80 p-1 shadow-[var(--landing-depth-1)] ring-1 ring-cyan-500/15 backdrop-blur-xl">
                <div
                  className="pointer-events-none absolute left-[1.45rem] top-12 bottom-12 hidden w-px bg-gradient-to-b from-cyan-500/60 via-violet-500/45 to-emerald-500/35 sm:block lg:left-[1.6rem]"
                  aria-hidden
                />
                <ol className="relative space-y-0 p-4 sm:p-5">
                  {pipeline.map((row, i) => (
                    <li
                      key={row.t}
                      className={cn(
                        "relative rounded-2xl border border-border/40 bg-background/45 px-3 py-3 sm:flex sm:items-center sm:gap-4 sm:py-2.5 sm:pl-2",
                        i > 0 && "mt-3",
                      )}
                    >
                      <div className="flex items-start gap-3 sm:items-center sm:gap-4">
                        <span
                          className={cn(
                            "relative z-[1] flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-[11px] font-bold ring-1 sm:h-11 sm:w-11",
                            row.c,
                            row.ring,
                          )}
                        >
                          {i + 1}
                        </span>
                        <div className="min-w-0 pt-0.5 sm:pt-0">
                          <p className="text-sm font-semibold text-foreground">{row.t}</p>
                          <p className="text-xs text-muted-foreground">{row.s}</p>
                        </div>
                      </div>
                    </li>
                  ))}
                </ol>
                <div className="pointer-events-none absolute -right-10 top-0 h-40 w-40 rounded-full bg-cyan-500/15 blur-3xl" />
                <div className="pointer-events-none absolute -bottom-8 left-1/4 h-28 w-28 rounded-full bg-violet-500/12 blur-2xl" />
              </div>
            </div>
          </LandingReveal>
        </div>
      </div>
    </section>
  );
}
