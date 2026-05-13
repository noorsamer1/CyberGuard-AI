"use client";

import { ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";

import { LandingReveal } from "@/components/landing/landing-reveal";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function LandingCta() {
  return (
    <section className="landing-section relative z-10 pb-12">
      <div className="mx-auto max-w-[var(--landing-max)] px-6 lg:px-8">
        <LandingReveal mode="cinema">
          <div className="relative overflow-hidden rounded-[2rem] border border-cyan-500/30 bg-gradient-to-br from-cyan-500/15 via-card/50 to-violet-600/15 p-[1px] shadow-[var(--landing-depth-1)] ring-1 ring-inset ring-white/[0.06]">
            <div className="relative rounded-[1.95rem] bg-gradient-to-br from-background/95 via-zinc-950/90 to-background/95 px-8 py-14 sm:px-12 lg:px-16 lg:py-16">
              <div className="pointer-events-none absolute -left-24 top-0 h-72 w-72 rounded-full bg-cyan-500/20 blur-3xl" />
              <div className="pointer-events-none absolute -right-20 bottom-0 h-64 w-64 rounded-full bg-violet-500/18 blur-3xl" />

              <div className="relative mx-auto max-w-3xl text-center">
                <p className="mx-auto mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-500/35 bg-cyan-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-cyan-100/95">
                  <Sparkles className="h-3.5 w-3.5" aria-hidden />
                  Ready when your cohort is
                </p>
                <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight text-foreground sm:text-4xl lg:text-[2.6rem] lg:leading-tight">
                  Ship a credible SOC narrative in a single afternoon
                </h2>
                <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-muted-foreground sm:text-lg">
                  Create an analyst account, load the bundled demo scenario from Settings, fire an Attack Lab campaign,
                  and walk alerts → incidents → PDF export live. No sales call required — the stack is in your repo.
                </p>
                <div className="mx-auto mt-10 grid max-w-xl grid-cols-3 gap-3 text-left sm:max-w-2xl">
                  {[
                    { label: "Time to first alert", value: "< 3 min" },
                    { label: "API surface", value: "OpenAPI" },
                    { label: "Deploy model", value: "Compose" },
                  ].map((s) => (
                    <div
                      key={s.label}
                      className="rounded-xl border border-border/50 bg-background/50 px-3 py-3 text-center backdrop-blur-sm"
                    >
                      <p className="font-[family-name:var(--font-display)] text-lg font-bold text-foreground sm:text-xl">
                        {s.value}
                      </p>
                      <p className="mt-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                        {s.label}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="mt-12 flex flex-wrap items-center justify-center gap-4">
                  <Link
                    href="/signup"
                    className={cn(
                      buttonVariants({ size: "lg" }),
                      "min-w-[220px] cursor-pointer bg-gradient-to-r from-cyan-500 to-cyan-600 px-10 text-base font-semibold text-primary-foreground shadow-xl shadow-cyan-500/30 hover:from-cyan-400 hover:to-cyan-500",
                    )}
                  >
                    Create free account <ArrowRight className="ml-2 h-4 w-4" aria-hidden />
                  </Link>
                  <Link
                    href="/login"
                    className={cn(
                      buttonVariants({ size: "lg", variant: "outline" }),
                      "cursor-pointer border-border/70 bg-background/50 px-8 text-base backdrop-blur-md hover:bg-background/85",
                    )}
                  >
                    I already have access
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </LandingReveal>
      </div>
    </section>
  );
}
