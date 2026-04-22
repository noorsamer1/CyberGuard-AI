import Link from "next/link";

import { CyberGuardLockup } from "@/components/branding/cyberguard-logo";

function apiDocsUrl() {
  const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";
  return `${base}/docs`;
}

const footerProduct = [
  { href: "#product", label: "Capabilities" },
  { href: "#how-it-works", label: "Pipeline" },
  { href: "#attack-lab", label: "Attack Lab" },
  { href: "#dashboard", label: "Dashboard" },
] as const;

const footerResources: readonly { href: string; label: string; external?: boolean }[] = [
  { href: "/learning", label: "Learning Lab" },
  { href: apiDocsUrl(), label: "OpenAPI docs", external: true },
  { href: "/login", label: "Sign in" },
  { href: "/signup", label: "Sign up" },
];

const footerExplore = [
  { href: "#proof", label: "Architecture proof" },
  { href: "#stack", label: "Stack" },
  { href: "#agents", label: "Agents" },
] as const;

export function LandingFooter() {
  return (
    <footer className="relative z-[2] border-t border-border/50 bg-gradient-to-b from-background/90 to-zinc-950/95 py-16 backdrop-blur-md">
      <div className="mx-auto grid max-w-6xl gap-12 px-6 sm:grid-cols-2 lg:grid-cols-4 lg:px-8">
        <div className="sm:col-span-2 lg:col-span-1">
          <Link href="/#top" className="inline-flex w-fit items-center gap-0 transition-opacity hover:opacity-90">
            <CyberGuardLockup variant="compact" />
          </Link>
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
            CyberGuard AI — teaching-grade security operations with real ingestion, detection, incidents, and exports.
          </p>
        </div>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">Product</p>
          <ul className="mt-4 space-y-2.5 text-sm text-muted-foreground">
            {footerProduct.map((l) => (
              <li key={l.href}>
                <Link href={l.href} className="transition-colors hover:text-foreground">
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">Resources</p>
          <ul className="mt-4 space-y-2.5 text-sm text-muted-foreground">
            {footerResources.map((l) => (
              <li key={l.label}>
                {l.external ? (
                  <a
                    href={l.href}
                    className="transition-colors hover:text-foreground"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {l.label}
                  </a>
                ) : (
                  <Link href={l.href} className="transition-colors hover:text-foreground">
                    {l.label}
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">Explore</p>
          <ul className="mt-4 space-y-2.5 text-sm text-muted-foreground">
            {footerExplore.map((l) => (
              <li key={l.href}>
                <Link href={l.href} className="transition-colors hover:text-foreground">
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="mx-auto mt-12 flex max-w-6xl flex-col items-start justify-between gap-4 border-t border-border/40 px-6 pt-8 text-xs text-muted-foreground lg:flex-row lg:items-center lg:px-8">
        <p>© {new Date().getFullYear()} CyberGuard AI.</p>
       
      </div>
    </footer>
  );
}
