"use client";

import { motion } from "framer-motion";
import { Activity, Gauge, LayoutDashboard, Radio } from "lucide-react";
import Link from "next/link";

import { useLandingScroll } from "@/components/landing/landing-scroll-context";
import { LandingReveal } from "@/components/landing/landing-reveal";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const mockBars = [
  { label: "Events", h: 40 },
  { label: "Alerts", h: 72 },
  { label: "Incidents", h: 28 },
];

export function LandingDashboardShowcase() {
  const reduced = useLandingScroll()?.reducedMotion ?? false;

  return (
    <section
      id="dashboard"
      className="landing-section relative z-10 scroll-mt-24 border-y border-border/40 bg-background/45 shadow-[var(--landing-depth-1)] backdrop-blur-md"
    >
      <div className="mx-auto max-w-[var(--landing-max)] px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-2 lg:items-start">
          <LandingReveal>
            <p className="landing-eyebrow mb-3 inline-flex items-center gap-2 text-cyan-300">
              <LayoutDashboard className="h-4 w-4" aria-hidden />
              Dashboard service
            </p>
            <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Operator cockpit backed by real aggregation logic
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">
              The React dashboard is not decorative charts on mock JSON — it binds to{" "}
              <code className="rounded-md border border-border/50 bg-muted/50 px-1.5 py-0.5 font-mono text-xs">
                dashboard_service.py
              </code>
              , which computes multi-window analytics, workload buckets, and anomaly counters scoped per analyst (
              <strong className="text-foreground">owner isolation</strong>). After you run an Attack Lab scenario,
              jump here to watch timelines, top detection rules, and exfiltration/auth signals update together.
            </p>
            <ul className="mt-6 space-y-3 text-sm text-muted-foreground">
              <li className="flex gap-2">
                <Gauge className="mt-0.5 h-4 w-4 shrink-0 text-cyan-400" aria-hidden />
                <span>
                  <strong className="text-foreground">MTTA / MTTR</strong> approximate analyst responsiveness from alert
                  state transitions and incident resolution timestamps.
                </span>
              </li>
              <li className="flex gap-2">
                <Radio className="mt-0.5 h-4 w-4 shrink-0 text-violet-300" aria-hidden />
                <span>
                  <strong className="text-foreground">Work queue cards</strong> mirror new vs acknowledged alerts and
                  open vs investigating incidents so students can narrate SOC load.
                </span>
              </li>
              <li className="flex gap-2">
                <Activity className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" aria-hidden />
                <span>
                  <strong className="text-foreground">Anomaly signals</strong> slice exfiltration, auth bursts,
                  outbound transfers, and privileged logins — ideal for capstone discussions on detection coverage gaps.
                </span>
              </li>
            </ul>
            <Link
              href="/signup"
              className={cn(
                buttonVariants({ size: "lg" }),
                "mt-8 inline-flex cursor-pointer bg-cyan-600 text-primary-foreground hover:bg-cyan-500",
              )}
            >
              Launch SOC cockpit
            </Link>
          </LandingReveal>

          <LandingReveal delay={0.08}>
            <div className="landing-hud-card landing-panel p-6 ring-1 ring-cyan-500/15">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Attack timeline</p>
                <span className="text-[10px] text-cyan-300">window: 24h</span>
              </div>
              <div className="mt-6 flex h-40 items-end gap-3">
                {mockBars.map((b, i) => (
                  <div key={b.label} className="flex flex-1 flex-col items-center gap-2">
                    <motion.div
                      className="w-full rounded-t-md bg-gradient-to-t from-cyan-600/30 to-cyan-400/80"
                      style={{ height: `${b.h}%`, transformOrigin: "50% 100%" }}
                      initial={reduced ? false : { scaleY: 0 }}
                      whileInView={reduced ? undefined : { scaleY: 1 }}
                      viewport={{ once: true }}
                      transition={{ delay: reduced ? 0 : 0.06 * i, duration: reduced ? 0 : 0.45, ease: "easeOut" }}
                    />
                    <span className="text-[10px] text-muted-foreground">{b.label}</span>
                  </div>
                ))}
              </div>
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-border/50 bg-background/40 p-3">
                  <p className="text-[10px] uppercase text-muted-foreground">Open alerts</p>
                  <p className="font-[family-name:var(--font-display)] text-2xl font-bold text-foreground">12</p>
                  <p className="text-[11px] text-muted-foreground">Queue pressure</p>
                </div>
                <div className="rounded-lg border border-border/50 bg-background/40 p-3">
                  <p className="text-[10px] uppercase text-muted-foreground">MTTA</p>
                  <p className="font-[family-name:var(--font-display)] text-2xl font-bold text-cyan-300">6.4m</p>
                  <p className="text-[11px] text-muted-foreground">Mean time to acknowledge</p>
                </div>
              </div>
              <p className="mt-4 text-[11px] leading-relaxed text-muted-foreground">
                Illustrative numbers — your tenant reflects the scenarios you execute and how fast students triage them.
              </p>
            </div>
          </LandingReveal>
        </div>
      </div>
    </section>
  );
}
