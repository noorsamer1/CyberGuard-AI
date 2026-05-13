"use client";

import { motion, useMotionValue, useTransform } from "framer-motion";
import { ArrowRight, Radio, Shield } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { useLandingScroll } from "@/components/landing/landing-scroll-context";
import { LandingReveal } from "@/components/landing/landing-reveal";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const heroStagger = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.09, delayChildren: 0.06 },
  },
};

const heroItem = {
  hidden: { opacity: 0, y: 26 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] as const },
  },
};

/**
 * Hero: video/blobs optional, Lenis-friendly scroll layer, staggered copy, HUD preview.
 */
export function LandingHero() {
  const [mounted, setMounted] = useState(false);
  const [videoAvailable, setVideoAvailable] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  const landing = useLandingScroll();
  const scrollFallback = useMotionValue(0);
  const scrollProgress = landing?.scrollYProgress ?? scrollFallback;
  const scrollReduced = landing?.reducedMotion ?? false;
  const parallaxOff = prefersReducedMotion || scrollReduced;
  const glowY = useTransform(scrollProgress, (p) => {
    if (parallaxOff) return 0;
    const t = Math.min(1, Math.max(0, p / 0.38));
    return t * 96;
  });
  const meshScale = useTransform(scrollProgress, (p) => {
    if (parallaxOff) return 1;
    return 1 + p * 0.04;
  });

  useEffect(() => {
    let cancelled = false;
    const frame = requestAnimationFrame(() => {
      if (cancelled) return;
      setMounted(true);
      setPrefersReducedMotion(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
      fetch("/hero.mp4", { method: "HEAD" })
        .then((res) => {
          if (!cancelled && res.ok) setVideoAvailable(true);
        })
        .catch(() => {});
    });
    return () => {
      cancelled = true;
      cancelAnimationFrame(frame);
    };
  }, []);

  const showFramerBlobs = mounted && !prefersReducedMotion && !videoAvailable;
  const showVideo = mounted && videoAvailable;
  const reduced = scrollReduced || prefersReducedMotion;

  return (
    <section
      id="top"
      className="landing-section relative z-10 flex min-h-[calc(100dvh-5rem)] flex-col justify-center px-6 pb-20 pt-8 lg:px-8"
    >
      <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        {showVideo ? (
          <video
            className="absolute inset-0 h-full w-full object-cover opacity-40"
            autoPlay
            muted
            loop
            playsInline
            poster="/hero-poster.jpg"
            aria-hidden
          >
            <source src="/hero.mp4" type="video/mp4" />
          </video>
        ) : null}

        <motion.div
          className="landing-hero-glow-layer absolute inset-0 bg-[radial-gradient(ellipse_90%_70%_at_50%_-15%,oklch(0.48_0.16_230_/_0.38),transparent_58%)]"
          style={{ y: glowY, scale: meshScale }}
          aria-hidden
        />
        <div
          className="absolute inset-0 bg-[radial-gradient(ellipse_55%_50%_at_100%_40%,oklch(0.42_0.2_290_/_0.14),transparent_55%)]"
          aria-hidden
        />

        {showFramerBlobs ? (
          <>
            <motion.div
              className="absolute -left-1/4 top-1/4 h-[30rem] w-[30rem] rounded-full bg-cyan-500/12 blur-3xl"
              animate={{ opacity: [0.35, 0.62, 0.35], scale: [1, 1.06, 1] }}
              transition={{ duration: 11, repeat: Infinity, ease: "easeInOut" }}
              aria-hidden
            />
            <motion.div
              className="absolute -right-1/4 bottom-[18%] h-[26rem] w-[26rem] rounded-full bg-violet-500/12 blur-3xl"
              animate={{ opacity: [0.32, 0.55, 0.32], scale: [1.04, 1, 1.04] }}
              transition={{ duration: 13, repeat: Infinity, ease: "easeInOut" }}
              aria-hidden
            />
          </>
        ) : null}

        <div
          className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23ffffff%22%20fill-opacity%3D%220.038%22%3E%3Cpath%20d%3D%22M36%2034v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6%2034v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6%204V0H4v4H0v2h4v4h2V6h4V4H6z%22%2F%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fsvg%3E')] opacity-95"
          aria-hidden
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/25 via-transparent to-background" aria-hidden />
      </div>

      <div className="mx-auto w-full max-w-[var(--landing-max)]">
        <LandingReveal mode="cinema">
          <div className="grid items-center gap-14 lg:grid-cols-[minmax(0,1.05fr)_minmax(300px,0.95fr)] lg:gap-16">
            {reduced ? (
              <div>
                <p className="landing-eyebrow mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-500/35 bg-cyan-500/10 px-4 py-1.5 text-cyan-200/95">
                  <Radio className="h-3.5 w-3.5" aria-hidden />
                  Security operations platform
                </p>
                <HeroCopy />
              </div>
            ) : (
              <motion.div variants={heroStagger} initial="hidden" animate="show">
                <motion.p
                  variants={heroItem}
                  className="landing-eyebrow mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-500/35 bg-cyan-500/10 px-4 py-1.5 text-cyan-200/95"
                >
                  <Radio className="h-3.5 w-3.5" aria-hidden />
                  Security operations platform
                </motion.p>
                <motion.div variants={heroItem}>
                  <HeroCopy />
                </motion.div>
              </motion.div>
            )}

            <LandingReveal mode="deep" delay={0.12} className="relative hidden min-w-0 lg:block">
              <div className="relative rounded-[1.75rem] border border-cyan-500/25 bg-gradient-to-br from-card/80 via-background/60 to-zinc-950/90 p-[1px] shadow-[var(--landing-depth-1)] ring-1 ring-inset ring-white/[0.06]">
                <div className="rounded-[1.7rem] bg-gradient-to-br from-zinc-950/95 via-background/90 to-zinc-950/95 p-1">
                  <div className="flex items-center gap-2 border-b border-white/10 bg-black/55 px-4 py-2.5">
                    <span className="h-2 w-2 rounded-full bg-rose-500/90" aria-hidden />
                    <span className="h-2 w-2 rounded-full bg-amber-400/90" aria-hidden />
                    <span className="h-2 w-2 rounded-full bg-emerald-500/85" aria-hidden />
                    <span className="ml-2 flex items-center gap-1.5 font-mono text-[10px] text-muted-foreground">
                      <Shield className="h-3 w-3 text-cyan-400/90" aria-hidden />
                      cyberguard / live console
                    </span>
                  </div>
                  <div className="space-y-2.5 p-5 font-mono text-[11px] leading-relaxed sm:text-xs">
                    <p>
                      <span className="text-zinc-500">ws://alerts</span>{" "}
                      <span className="text-emerald-300/90">SUBSCRIBE</span> ack
                      <span className="text-muted-foreground"> · tenant_isolation=on</span>
                    </p>
                    <p>
                      <span className="text-zinc-500">[12:01:04]</span>{" "}
                      <span className="text-cyan-300/95">RULE</span> port_scan ·{" "}
                      <span className="text-amber-200/90">src 10.0.2.15</span>
                    </p>
                    <p>
                      <span className="text-zinc-500">[12:01:06]</span>{" "}
                      <span className="text-violet-300/95">INCIDENT</span> CG-204 opened ·{" "}
                      <span className="text-rose-300/95">sev high</span>
                    </p>
                    <p>
                      <span className="text-zinc-500">[12:01:11]</span>{" "}
                      <span className="text-cyan-200/80">PDF</span> queued · digest window +00:30
                    </p>
                    <p className="border-t border-white/5 pt-2.5 text-muted-foreground">
                      OpenRouter briefing optional — structured JSON merged into incident narrative.
                    </p>
                  </div>
                </div>
              </div>
              <div className="pointer-events-none absolute -right-6 -top-10 h-44 w-44 rounded-full bg-cyan-500/18 blur-3xl" />
              <div className="pointer-events-none absolute -bottom-10 -left-4 h-36 w-36 rounded-full bg-violet-500/14 blur-2xl" />
            </LandingReveal>
          </div>
        </LandingReveal>
      </div>
    </section>
  );
}

function HeroCopy() {
  return (
    <>
      <h1 className="font-[family-name:var(--font-display)] text-4xl font-bold leading-[1.05] tracking-[-0.035em] text-foreground sm:text-5xl lg:text-[3.45rem] xl:text-[3.75rem]">
        <span className="block">Operate your SOC with</span>
        <span className="mt-1 block">
          <span className="bg-gradient-to-r from-cyan-200 via-cyan-300 to-cyan-100 bg-clip-text text-transparent">
            clarity
          </span>
          <span className="text-muted-foreground/85"> & </span>
          <span className="bg-gradient-to-r from-violet-300 via-fuchsia-300 to-violet-200 bg-clip-text text-transparent">
            speed
          </span>
        </span>
      </h1>
      <p className="mt-7 max-w-xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
        A full-stack console that actually ships: FastAPI services with OpenAPI contracts, Next.js dashboards, Postgres
        persistence, Redis-backed jobs, and WebSocket alert fan-out. Run{" "}
        <Link href="#attack-lab" className="font-medium text-cyan-300 underline-offset-4 hover:underline">
          MITRE-aligned scenarios
        </Link>
        , triage in the{" "}
        <Link href="#dashboard" className="font-medium text-cyan-300 underline-offset-4 hover:underline">
          operator cockpit
        </Link>
        , then export evidence or grade analysts in the{" "}
        <Link href="/learning" className="font-medium text-cyan-300 underline-offset-4 hover:underline">
          Learning Lab
        </Link>
        .
      </p>
      <div className="mt-8 grid max-w-xl grid-cols-3 gap-3 sm:flex sm:flex-wrap sm:gap-2">
        {[
          { k: "Rules", v: "5+" },
          { k: "Severities", v: "4" },
          { k: "Exports", v: "PDF" },
        ].map((m) => (
          <div
            key={m.k}
            className="rounded-xl border border-border/50 bg-background/50 px-3 py-2 text-center shadow-inner shadow-black/20 backdrop-blur-sm sm:min-w-[5.5rem]"
          >
            <p className="font-[family-name:var(--font-display)] text-lg font-bold text-foreground sm:text-xl">{m.v}</p>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{m.k}</p>
          </div>
        ))}
      </div>
      <div className="mt-8 flex flex-wrap gap-2">
        {["Async FastAPI + Celery", "JWT + owner isolation", "Docker Compose ready"].map((label) => (
          <span
            key={label}
            className="inline-flex items-center rounded-full border border-border/55 bg-card/40 px-3 py-1 text-[11px] font-medium text-muted-foreground backdrop-blur-sm"
          >
            {label}
          </span>
        ))}
      </div>
      <div className="mt-10 flex flex-wrap items-center gap-4">
        <Link
          href="/signup"
          className={cn(
            buttonVariants({ size: "lg" }),
            "h-12 min-w-[190px] cursor-pointer bg-gradient-to-r from-cyan-500 to-cyan-600 px-8 text-base font-semibold text-primary-foreground shadow-xl shadow-cyan-500/30 hover:from-cyan-400 hover:to-cyan-500",
          )}
        >
          Launch console <ArrowRight className="ml-2 h-4 w-4" aria-hidden />
        </Link>
        <Link
          href="/login"
          className={cn(
            buttonVariants({ size: "lg", variant: "outline" }),
            "h-12 cursor-pointer border-border/70 bg-background/55 px-8 text-base backdrop-blur-md hover:bg-background/85",
          )}
        >
          Sign in to demo
        </Link>
      </div>
    </>
  );
}
