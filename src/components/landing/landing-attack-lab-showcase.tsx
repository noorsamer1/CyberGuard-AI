"use client";

import { FlaskConical, Play } from "lucide-react";
import Link from "next/link";

import { LandingAttackInteractiveDemo } from "@/components/landing/landing-attack-interactive-demo";
import { LandingReveal } from "@/components/landing/landing-reveal";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function LandingAttackLabShowcase() {
  return (
    <section
      id="attack-lab"
      className="landing-section relative z-10 scroll-mt-24 border-y border-border/30 bg-gradient-to-b from-background/25 via-transparent to-background/35 shadow-[var(--landing-depth-1)]"
    >
      <div className="mx-auto grid max-w-[var(--landing-max)] gap-12 px-6 lg:grid-cols-2 lg:items-start lg:px-8">
        <LandingReveal>
          <p className="landing-eyebrow mb-3 inline-flex items-center gap-2 text-violet-300">
            <FlaskConical className="h-4 w-4" aria-hidden />
            Attack Lab
          </p>
          <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Launch synthetic campaigns with teaching-grade context
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">
            The Attack Lab calls the same ingestion path as production telemetry:{" "}
            <code className="rounded-md border border-border/50 bg-muted/50 px-1.5 py-0.5 font-mono text-xs">
              POST /api/v1/scenarios/&lt;scenario_id&gt;/run
            </code>
            . Each bundle includes realistic auth, network, and DLP-style signals. Detection rules (for example{" "}
            <span className="text-cyan-300">data_exfiltration</span>, brute force, port scan) raise alerts you can
            acknowledge, resolve, and escalate into incidents.
          </p>
          <ul className="mt-6 space-y-3 text-sm text-muted-foreground">
            <li className="flex gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" aria-hidden />
              <span>
                <strong className="text-foreground">MITRE ATT&CK</strong> chips map to teaching notes: objectives,
                flows, and detection focus per scenario.
              </span>
            </li>
            <li className="flex gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" aria-hidden />
              <span>
                The <strong className="text-foreground">interactive runner</strong> on the right is fully in the
                browser: pick a scenario, hit run, watch the scripted terminal and preview feed — no sign-in required on
                this page.
              </span>
            </li>
          </ul>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/attack-lab"
              className={cn(
                buttonVariants({ size: "lg" }),
                "cursor-pointer bg-gradient-to-r from-violet-600 to-cyan-600 text-primary-foreground shadow-lg shadow-violet-500/25",
              )}
            >
              <Play className="mr-2 h-4 w-4" aria-hidden />
              Open Attack Lab
            </Link>
            <Link
              href="/login"
              className={cn(buttonVariants({ variant: "outline", size: "lg" }), "cursor-pointer border-border/70")}
            >
              Already have an account? Sign in
            </Link>
          </div>
        </LandingReveal>

        <LandingReveal delay={0.08} className="lg:pt-2">
          <LandingAttackInteractiveDemo />
        </LandingReveal>
      </div>
    </section>
  );
}
