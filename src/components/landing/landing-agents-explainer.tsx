"use client";

import type { LucideIcon } from "lucide-react";
import { Crosshair, FileText, LayoutDashboard, Swords } from "lucide-react";

import { LandingReveal } from "@/components/landing/landing-reveal";

type AgentCard = {
  name: string;
  icon: LucideIcon;
  detail: string;
};

const agents: readonly AgentCard[] = [
  {
    name: "Attack Scenario Simulator",
    icon: Swords,
    detail:
      "Curated bundles + Attack Lab UI fire the same ingestion and detection pipeline students will see in alerts/incidents.",
  },
  {
    name: "MITRE ATT&CK Intelligence",
    icon: Crosshair,
    detail:
      "Rule-to-technique mapping enriches alerts and incidents so analysts can pivot to official ATT&CK pages with context.",
  },
  {
    name: "Threat Report & Executive Briefing",
    icon: FileText,
    detail:
      "Incident briefing endpoint distills technical and executive narratives plus learning benchmarks for stakeholder-ready storytelling.",
  },
  {
    name: "Operator dashboard & UI copilot",
    icon: LayoutDashboard,
    detail:
      "The productized cockpit renders real aggregation output—timelines, workload, exfiltration and auth signals, MITRE coverage—while in-product recommendations react to queue depth and posture to suggest the next high-value screen.",
  },
];

export function LandingAgentsExplainer() {
  return (
    <section
      id="agents"
      className="landing-section relative z-10 scroll-mt-24 border-y border-border/30 bg-gradient-to-b from-transparent via-violet-500/[0.04] to-transparent shadow-[var(--landing-depth-1)]"
    >
      <div className="mx-auto max-w-[var(--landing-max)] px-6 lg:px-8">
        <LandingReveal>
          <div className="mx-auto mb-12 max-w-2xl text-center">
            <p className="landing-eyebrow text-violet-300">Agentic surface area</p>
            <h2 className="mt-3 font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Four coordinated experiences, one SOC spine
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">
              Each surface is intentionally narrow: deterministic backend services plus focused UI affordances. Together
              they show how modern SOCs blend automation, intelligence, and human judgment without hiding the plumbing.
            </p>
          </div>
        </LandingReveal>
        <div className="grid gap-5 sm:grid-cols-2">
          {agents.map((agent, i) => (
            <LandingReveal key={agent.name} delay={0.04 * i}>
              <article className="landing-panel flex gap-4 p-5 ring-1 ring-white/5 transition-colors hover:border-violet-500/30">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-500/15 ring-1 ring-violet-500/25">
                  <agent.icon className="h-5 w-5 text-violet-200" aria-hidden />
                </div>
                <div>
                  <h3 className="font-[family-name:var(--font-display)] text-base font-semibold text-foreground">
                    {agent.name}
                  </h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{agent.detail}</p>
                </div>
              </article>
            </LandingReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
