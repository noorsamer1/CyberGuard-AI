"use client";

import { motion } from "framer-motion";
import { Activity, Brain, Radio } from "lucide-react";

import { useLandingScroll } from "@/components/landing/landing-scroll-context";
import { LandingReveal } from "@/components/landing/landing-reveal";
import { cn } from "@/lib/utils";

const pillars = [
  {
    title: "Ingest & normalize",
    icon: Radio,
    iconClass: "text-cyan-300",
    accent: "from-cyan-500/30 to-cyan-500/5",
    border: "border-cyan-500/35",
    topBar: "from-cyan-400 via-cyan-200 to-transparent",
    dot: "bg-cyan-400/90",
    bullets: [
      "REST batch ingest and CSV / line uploads with schema validation",
      "Synthetic Attack Lab bundles mirror production field shapes",
      "Structured fields: IP, user, port, type, severity, MITRE hints",
    ],
    gridClass: "lg:col-span-7",
  },
  {
    title: "Detect & escalate",
    icon: Activity,
    iconClass: "text-violet-300",
    accent: "from-violet-500/30 to-violet-500/5",
    border: "border-violet-500/35",
    topBar: "from-violet-400 via-fuchsia-300 to-transparent",
    dot: "bg-violet-400/90",
    bullets: [
      "Modular rules: brute force, port scan, denied spikes, rate anomaly",
      "WebSocket alert lifecycle for triage dashboards",
      "High / critical severities open incidents with SLA timers",
    ],
    gridClass: "lg:col-span-5",
  },
  {
    title: "Analyze & report",
    icon: Brain,
    iconClass: "text-fuchsia-300",
    accent: "from-fuchsia-500/25 to-fuchsia-500/5",
    border: "border-fuchsia-500/35",
    topBar: "from-fuchsia-400 via-rose-300 to-transparent",
    dot: "bg-fuchsia-400/90",
    bullets: [
      "Optional OpenRouter JSON briefings merged into incidents",
      "Incident PDFs with charts, tables, and executive summaries",
      "SMTP digests when outbound mail is configured",
    ],
    gridClass: "lg:col-span-12",
  },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, y: 28 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.48, ease: [0.16, 1, 0.3, 1] as const },
  },
};

function PillarCard({
  p,
  className,
}: {
  p: (typeof pillars)[number];
  className?: string;
}) {
  return (
    <article
      className={cn(
        "group relative flex h-full min-h-[14rem] flex-col overflow-hidden rounded-3xl border bg-card/50 p-8 ring-1 ring-white/[0.05] backdrop-blur-xl transition-[transform,box-shadow,border-color] duration-300 hover:-translate-y-0.5 hover:shadow-[var(--landing-depth-glow)]",
        p.border,
        className,
      )}
    >
      <div
        className={cn("pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r opacity-95", p.topBar)}
        aria-hidden
      />
      <div
        className={cn(
          "mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ring-1 ring-white/10 transition-transform duration-300 group-hover:scale-[1.04]",
          p.accent,
        )}
      >
        <p.icon className={cn("h-7 w-7", p.iconClass)} aria-hidden />
      </div>
      <h3 className="font-[family-name:var(--font-display)] text-2xl font-semibold tracking-tight text-foreground">
        {p.title}
      </h3>
      <ul className="mt-6 flex flex-1 flex-col gap-3.5 text-sm leading-relaxed text-muted-foreground">
        {p.bullets.map((b) => (
          <li key={b} className="flex gap-2.5">
            <span className={cn("mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full", p.dot)} aria-hidden />
            <span>{b}</span>
          </li>
        ))}
      </ul>
    </article>
  );
}

export function LandingPillars() {
  const reduced = useLandingScroll()?.reducedMotion ?? false;

  return (
    <section className="landing-section relative z-10">
      <div className="mx-auto max-w-[var(--landing-max)] px-6 lg:px-8">
        <LandingReveal mode="deep">
          <div className="mx-auto max-w-3xl text-center lg:max-w-4xl">
            <p className="landing-eyebrow text-muted-foreground">What you get</p>
            <h2 className="mt-3 font-[family-name:var(--font-display)] text-3xl font-bold tracking-[-0.03em] text-foreground sm:text-4xl lg:text-[2.5rem]">
              A bento of capabilities that map to real services in this repo
            </h2>
            <p className="mt-5 text-base leading-relaxed text-muted-foreground sm:text-lg">
              Each tile below corresponds to deployable modules: ingestion workers, detection packages, alert fan-out,
              incident workflows, and reporting pipelines. This is the same language we use inside architecture reviews
              — no buzzword soup.
            </p>
          </div>
        </LandingReveal>

        {reduced ? (
          <div className="mt-14 grid gap-6 lg:grid-cols-12">
            {pillars.map((p) => (
              <PillarCard key={p.title} p={p} className={p.gridClass} />
            ))}
          </div>
        ) : (
          <motion.div
            className="mt-14 grid gap-6 lg:grid-cols-12"
            variants={container}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-10% 0px" }}
          >
            {pillars.map((p) => (
              <motion.div key={p.title} variants={item} className={cn("min-h-0", p.gridClass)}>
                <PillarCard p={p} className="h-full" />
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </section>
  );
}
