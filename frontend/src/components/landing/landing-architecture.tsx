"use client";

import { Cpu, Database, Layers, Server } from "lucide-react";

import { LandingReveal } from "@/components/landing/landing-reveal";

const layers = [
  {
    title: "Presentation",
    body: "Next.js App Router, TanStack Query, Framer Motion on the console; public landing explains each module before sign-in.",
    icon: Layers,
  },
  {
    title: "API plane",
    body: "FastAPI `/api/v1` — JWT auth, scoped CRUD, WebSocket fan-out for live alerts, Celery tasks for AI PDFs and digests.",
    icon: Server,
  },
  {
    title: "Detection & analytics",
    body: "Rule engine evaluates ingested events; `dashboard_service` aggregates MTTA/MTTR, timelines, work queues, and MITRE coverage for charts.",
    icon: Cpu,
  },
  {
    title: "Persistence",
    body: "PostgreSQL for events, alerts, incidents, exercises, reports; Redis for brokered jobs.",
    icon: Database,
  },
];

export function LandingArchitecture() {
  return (
    <section
      id="stack"
      className="landing-section relative z-10 scroll-mt-24 border-y border-border/25 bg-background/30 shadow-[var(--landing-depth-1)] backdrop-blur-sm"
    >
      <div className="mx-auto max-w-[var(--landing-max)] px-6 lg:px-8">
        <LandingReveal>
          <div className="mx-auto mb-12 max-w-2xl text-center">
            <p className="landing-eyebrow text-cyan-400/90">Architecture</p>
            <h2 className="mt-3 font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              How CyberGuard is wired end-to-end
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">
              Educational demos still deserve a believable stack: ingest → detect → alert → incident → optional AI
              analysis → PDFs. The landing page mirrors that story so instructors can orient students in one pass.
            </p>
          </div>
        </LandingReveal>
        <div className="grid gap-6 sm:grid-cols-2">
          {layers.map((row, i) => (
            <LandingReveal key={row.title} delay={0.05 * i}>
              <article className="landing-panel cursor-default p-6 ring-1 ring-white/5 transition-colors hover:border-cyan-500/25">
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/15 ring-1 ring-cyan-500/25">
                  <row.icon className="h-5 w-5 text-cyan-300" aria-hidden />
                </div>
                <h3 className="font-[family-name:var(--font-display)] text-lg font-semibold text-foreground">
                  {row.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{row.body}</p>
              </article>
            </LandingReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
