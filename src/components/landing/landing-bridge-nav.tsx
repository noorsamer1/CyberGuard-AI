"use client";

import Link from "next/link";
import { Compass } from "lucide-react";

import { LANDING_IN_PAGE_LINKS } from "@/components/landing/landing-nav-links";
import { cn } from "@/lib/utils";

export function LandingBridgeNav() {
  return (
    <nav
      className="sticky z-[25] border-b border-border/45 bg-background/65 backdrop-blur-xl supports-[backdrop-filter]:bg-background/50"
      style={{ top: "var(--landing-header-h, 4.75rem)" }}
      aria-label="Section shortcuts"
    >
      <div className="mx-auto flex max-w-[var(--landing-max)] flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4 lg:px-8">
        <div className="flex items-center gap-2 text-muted-foreground">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-cyan-500/25 bg-cyan-500/10 text-cyan-300/95">
            <Compass className="h-4 w-4" aria-hidden />
          </span>
          <div className="min-w-0 leading-tight">
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-cyan-200/85">Explore</p>
            <p className="text-xs text-muted-foreground/90">Jump to product areas on this page</p>
          </div>
        </div>
        <ul className="flex max-w-full snap-x snap-mandatory gap-2 overflow-x-auto pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none] sm:justify-end sm:pb-0 [&::-webkit-scrollbar]:hidden">
          {LANDING_IN_PAGE_LINKS.map((item) => (
            <li key={item.href} className="snap-start">
              <Link
                href={item.href}
                className={cn(
                  "inline-flex cursor-pointer whitespace-nowrap rounded-xl border border-border/50 bg-gradient-to-b from-card/70 to-card/30 px-3.5 py-2 text-xs font-semibold text-muted-foreground shadow-sm shadow-black/15 transition-all duration-200",
                  "hover:border-cyan-500/40 hover:bg-cyan-500/10 hover:text-foreground hover:shadow-cyan-500/10",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50",
                )}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
