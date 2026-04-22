"use client";

import Link from "next/link";
import { Menu } from "lucide-react";
import { useState } from "react";

import { CyberGuardLockup } from "@/components/branding/cyberguard-logo";
import { LANDING_IN_PAGE_LINKS } from "@/components/landing/landing-nav-links";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

export function LandingHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 border-b border-border/30 bg-background/70 backdrop-blur-xl supports-[backdrop-filter]:bg-background/55">
      <div className="mx-auto flex max-w-[var(--landing-max)] items-center justify-between gap-3 px-6 py-4 lg:px-8">
        <Link
          href="/#top"
          className="flex min-w-0 shrink-0 items-center gap-1 transition-opacity hover:opacity-90"
          aria-label="CyberGuard AI home"
        >
          <CyberGuardLockup />
        </Link>

        <nav className="hidden items-center gap-3 md:flex" aria-label="Primary">
          <div className="flex flex-wrap items-center gap-0.5 rounded-full border border-border/45 bg-card/35 px-1 py-1 shadow-inner shadow-black/20 backdrop-blur-md">
            {LANDING_IN_PAGE_LINKS.map((a) => (
              <Link
                key={a.href}
                href={a.href}
                className="rounded-full px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground transition-colors hover:bg-cyan-500/12 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/45"
              >
                {a.label}
              </Link>
            ))}
          </div>
          <Link href="/login" className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "text-muted-foreground")}>
            Sign in
          </Link>
          <Link
            href="/signup"
            className={cn(
              buttonVariants({ size: "sm" }),
              "bg-gradient-to-r from-cyan-500 to-cyan-600 text-primary-foreground shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-cyan-500",
            )}
          >
            Get started
          </Link>
        </nav>

        <div className="flex items-center gap-2 md:hidden">
          <Link href="/login" className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "text-muted-foreground")}>
            Sign in
          </Link>
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger
              nativeButton
              render={<Button variant="outline" size="icon-sm" className="border-border/60" aria-label="Open menu" />}
            >
              <Menu className="size-5" />
            </SheetTrigger>
            <SheetContent side="right" className="w-[min(100%,20rem)] border-border/60">
              <SheetHeader>
                <SheetTitle className="font-[family-name:var(--font-display)]">Navigate</SheetTitle>
              </SheetHeader>
              <nav className="flex flex-col px-2 pb-4" aria-label="Mobile section links">
                {LANDING_IN_PAGE_LINKS.map((a) => (
                  <Link
                    key={a.href}
                    href={a.href}
                    className="rounded-md px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-cyan-500/10 hover:text-foreground"
                    onClick={() => setMobileOpen(false)}
                  >
                    {a.label}
                  </Link>
                ))}
              </nav>
              <div className="mt-2 flex flex-col gap-2 border-t border-border/40 p-4">
                <Link href="/signup" onClick={() => setMobileOpen(false)} className={cn(buttonVariants(), "w-full")}>
                  Get started
                </Link>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
