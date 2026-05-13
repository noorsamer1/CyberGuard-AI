"use client";

import type { MotionValue } from "framer-motion";
import { createContext, useContext } from "react";

export type LandingScrollContextValue = {
  scrollYProgress: MotionValue<number>;
  reducedMotion: boolean;
};

const LandingScrollContext = createContext<LandingScrollContextValue | null>(null);

export function useLandingScroll(): LandingScrollContextValue | null {
  return useContext(LandingScrollContext);
}

export { LandingScrollContext };
