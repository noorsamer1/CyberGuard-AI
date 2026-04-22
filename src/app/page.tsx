import { Plus_Jakarta_Sans } from "next/font/google";

import { LandingAgentsExplainer } from "@/components/landing/landing-agents-explainer";
import { LandingArchitecture } from "@/components/landing/landing-architecture";
import { LandingAttackLabShowcase } from "@/components/landing/landing-attack-lab-showcase";
import { LandingBridgeNav } from "@/components/landing/landing-bridge-nav";
import { LandingCta } from "@/components/landing/landing-cta";
import { LandingDashboardShowcase } from "@/components/landing/landing-dashboard-showcase";
import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingHeader } from "@/components/landing/landing-header";
import { LandingHero } from "@/components/landing/landing-hero";
import { LandingHowItWorksRail } from "@/components/landing/landing-how-it-works-rail";
import { LandingMarquee } from "@/components/landing/landing-marquee";
import { LandingMission } from "@/components/landing/landing-mission";
import { LandingPillars } from "@/components/landing/landing-pillars";
import { LandingScrollRoot } from "@/components/landing/landing-scroll-root";
import { LandingStats } from "@/components/landing/landing-stats";
import { LandingTrustBar } from "@/components/landing/landing-trust-bar";
import { cn } from "@/lib/utils";

const landingSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-landing-sans",
  display: "swap",
});

export default function LandingPage() {
  return (
    <div
      className={cn(
        "landing-cyber-root landing-type-body relative min-h-screen overflow-x-hidden bg-[radial-gradient(ellipse_120%_80%_at_50%_-20%,oklch(0.22_0.06_260)_0%,oklch(0.12_0.04_260)_42%,oklch(0.09_0.02_260)_100%)]",
        landingSans.variable,
      )}
    >
      <div className="landing-cyber-grid" aria-hidden />
      <div className="landing-cyber-scanlines" aria-hidden />
      <LandingScrollRoot>
        <LandingHeader />
        <main className="relative z-[2]">
          <LandingHero />
          <LandingBridgeNav />
          <div id="product" className="scroll-mt-[var(--landing-header-h)]">
            <LandingStats />
            <LandingTrustBar />
            <LandingMission />
            <LandingPillars />
          </div>
          <LandingHowItWorksRail />
          <LandingAttackLabShowcase />
          <LandingDashboardShowcase />
          <LandingAgentsExplainer />
          <LandingArchitecture />
          <LandingMarquee />
          <LandingCta />
        </main>
        <LandingFooter />
      </LandingScrollRoot>
    </div>
  );
}
