"use client";

import { Award, BookOpen, Fingerprint, ShieldCheck } from "lucide-react";

import { LandingReveal } from "@/components/landing/landing-reveal";

const proofPoints = [
  {
    icon: ShieldCheck,
    title: "Deterministic detection first",
    body: "Rules ship in-repo (`detection/rules`) with explicit thresholds — no black-box scores. AI summaries are optional overlays on top of structured incidents.",
  },
  {
    icon: Fingerprint,
    title: "JWT-scoped analyst plane",
    body: "Dashboard aggregates, alert queues, and incident timelines respect owner isolation so classroom tenants do not leak into each other’s views.",
  },
  {
    icon: BookOpen,
    title: "Teaching-native flows",
    body: "Attack Lab scenarios call the same `/api/v1/scenarios/.../run` path as scripted exercises; Learning Lab captures graded analyst journeys for capstone rubrics.",
  },
  {
    icon: Award,
    title: "Evidence you can export",
    body: "Incident PDFs bundle charts, event tables, and optional OpenRouter narratives — suitable for stakeholder decks or lab submission packets.",
  },
];

export function LandingTrustBar() {
  return (
    <section
      id="proof"
      className="relative z-10 scroll-mt-24 border-y border-cyan-500/15 bg-gradient-to-b from-cyan-500/[0.07] via-transparent to-transparent py-16"
      aria-labelledby="trust-heading"
    >
      <div className="mx-auto max-w-[var(--landing-max)] px-6 lg:px-8">
        <LandingReveal mode="deep">
          <div className="flex flex-col gap-4 text-center lg:text-left">
            <p className="landing-eyebrow text-cyan-200/90">Signal, not slogans</p>
            <h2
              id="trust-heading"
              className="font-[family-name:var(--font-display)] text-2xl font-bold tracking-tight text-foreground sm:text-3xl lg:text-[2rem] lg:leading-snug"
            >
              Built for instructors, blue teams, and product evaluators who read the schema
            </h2>
            <p className="mx-auto max-w-3xl text-sm leading-relaxed text-muted-foreground lg:mx-0 lg:max-w-2xl lg:text-base">
              CyberGuard is intentionally opinionated: PostgreSQL as system of record, Redis-backed jobs, WebSocket fan-out
              for alerts, and OpenAPI you can diff against your own SOC tooling. The points below are architectural facts,
              not aspirational marketing.
            </p>
          </div>
        </LandingReveal>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {proofPoints.map((row, i) => (
            <LandingReveal key={row.title} delay={0.06 * i} mode="deep">
              <article className="group relative flex h-full flex-col overflow-hidden rounded-2xl border border-border/50 bg-card/40 p-5 shadow-[var(--landing-depth-1)] ring-1 ring-white/[0.04] backdrop-blur-md transition-[transform,box-shadow,border-color] duration-300 hover:-translate-y-0.5 hover:border-cyan-500/30 hover:shadow-[var(--landing-depth-glow)]">
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/12 text-cyan-200 ring-1 ring-cyan-400/25 transition-transform duration-300 group-hover:scale-105">
                  <row.icon className="h-5 w-5" aria-hidden />
                </div>
                <h3 className="font-[family-name:var(--font-display)] text-base font-semibold tracking-tight text-foreground">
                  {row.title}
                </h3>
                <p className="mt-2 flex-1 text-xs leading-relaxed text-muted-foreground sm:text-sm">{row.body}</p>
              </article>
            </LandingReveal>
          ))}
        </div>

        <LandingReveal mode="normal" delay={0.2} className="mt-12">
          <div className="flex flex-col items-center justify-between gap-4 rounded-2xl border border-dashed border-border/60 bg-background/40 px-6 py-5 text-center sm:flex-row sm:text-left">
            <p className="max-w-2xl text-xs leading-relaxed text-muted-foreground sm:text-sm">
              <strong className="text-foreground">Placeholder social proof:</strong> “We replaced three static slide
              decks with one CyberGuard walkthrough for our incident-response module.” — Security program lead (anon
              pilot). Swap with real quotes when you have permission to publish names.
            </p>
            <div className="flex shrink-0 flex-wrap justify-center gap-2">
              {["MITRE ATT&CK mapping", "NIST-style triage", "Docker Compose day-0"].map((chip) => (
                <span
                  key={chip}
                  className="rounded-full border border-border/50 bg-muted/30 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground"
                >
                  {chip}
                </span>
              ))}
            </div>
          </div>
        </LandingReveal>
      </div>
    </section>
  );
}
