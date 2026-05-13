"use client";

import Lenis from "lenis";
import { motion, useScroll, useSpring } from "framer-motion";
import { useEffect, useMemo, useSyncExternalStore } from "react";

import { LandingScrollContext } from "@/components/landing/landing-scroll-context";

import "lenis/dist/lenis.css";

function subscribeReducedMotion(onStoreChange: () => void) {
  const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  mq.addEventListener("change", onStoreChange);
  return () => mq.removeEventListener("change", onStoreChange);
}

function getReducedMotionSnapshot(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function getReducedMotionServerSnapshot(): boolean {
  return false;
}

type LandingScrollRootProps = {
  children: React.ReactNode;
};

/**
 * Public landing shell: Lenis smooth scroll, scroll progress for parallax/reveals,
 * and a slim progress bar (hidden when reduced motion).
 */
export function LandingScrollRoot({ children }: LandingScrollRootProps) {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 120,
    damping: 32,
    restDelta: 0.0005,
  });
  const reducedMotion = useSyncExternalStore(
    subscribeReducedMotion,
    getReducedMotionSnapshot,
    getReducedMotionServerSnapshot,
  );

  const value = useMemo(
    () => ({ scrollYProgress, reducedMotion }),
    [scrollYProgress, reducedMotion],
  );

  useEffect(() => {
    const el = document.documentElement;
    el.classList.add("landing-snap-scroll");
    return () => {
      el.classList.remove("landing-snap-scroll");
    };
  }, []);

  useEffect(() => {
    if (reducedMotion) return undefined;

    const lenis = new Lenis({
      duration: 1.15,
      smoothWheel: true,
      wheelMultiplier: 0.92,
      touchMultiplier: 1.85,
      lerp: 0.09,
    });

    let rafId = 0;
    const raf = (time: number) => {
      lenis.raf(time);
      rafId = requestAnimationFrame(raf);
    };
    rafId = requestAnimationFrame(raf);

    return () => {
      cancelAnimationFrame(rafId);
      lenis.destroy();
    };
  }, [reducedMotion]);

  return (
    <LandingScrollContext.Provider value={value}>
      {!reducedMotion ? (
        <motion.div
          className="pointer-events-none fixed left-0 right-0 top-0 z-[100] h-[3px] origin-left bg-gradient-to-r from-cyan-400 via-sky-400 to-violet-500 opacity-95 shadow-[0_0_24px_oklch(0.72_0.14_230_/_0.45)]"
          style={{ scaleX, transformOrigin: "0% 50%" }}
          aria-hidden
        />
      ) : null}
      {children}
    </LandingScrollContext.Provider>
  );
}
