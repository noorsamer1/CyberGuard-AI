"use client";

import { motion, type HTMLMotionProps, type Variant } from "framer-motion";

import { useLandingScroll } from "@/components/landing/landing-scroll-context";

const variantsNormal: Record<string, Variant> = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0 },
};

const variantsDeep: Record<string, Variant> = {
  hidden: { opacity: 0, y: 48, scale: 0.97 },
  show: { opacity: 1, y: 0, scale: 1 },
};

const variantsCinema: Record<string, Variant> = {
  hidden: { opacity: 0, y: 56, scale: 0.96, filter: "blur(12px)" },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    filter: "blur(0px)",
    transition: { duration: 0.75, ease: [0.16, 1, 0.3, 1] },
  },
};

export type LandingRevealProps = HTMLMotionProps<"div"> & {
  /** Stagger order when used with parent staggerChildren */
  delay?: number;
  /** Scroll-linked entrance intensity */
  mode?: "normal" | "deep" | "cinema";
};

/**
 * Scroll-triggered section reveal with easing tuned for premium landing motion.
 */
export function LandingReveal({ children, className, delay = 0, mode = "normal", ...rest }: LandingRevealProps) {
  const ctx = useLandingScroll();
  const reduced = ctx?.reducedMotion ?? false;

  const variants =
    mode === "cinema" ? variantsCinema : mode === "deep" ? variantsDeep : variantsNormal;
  const duration = mode === "cinema" ? 0.72 : mode === "deep" ? 0.62 : 0.52;

  return (
    <motion.div
      initial={reduced ? false : "hidden"}
      whileInView={reduced ? undefined : "show"}
      viewport={{ once: true, margin: "-12% 0px -8% 0px", amount: 0.12 }}
      variants={reduced ? undefined : variants}
      transition={{
        duration: reduced ? 0 : duration,
        delay: reduced ? 0 : delay,
        ease: [0.16, 1, 0.3, 1],
      }}
      className={className}
      {...rest}
    >
      {children}
    </motion.div>
  );
}
