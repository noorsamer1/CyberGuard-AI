"use client";

import Link from "next/link";
import { Plus_Jakarta_Sans } from "next/font/google";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRight, Plug, Radar, UserPlus } from "lucide-react";
import { toast } from "sonner";

import { CyberGuardLockup } from "@/components/branding/cyberguard-logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch, setTokens } from "@/lib/api/client";
import type { User } from "@/lib/api/types";
import { useAuthStore } from "@/store/auth-store";
import { cn } from "@/lib/utils";

const landingSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-landing-sans",
  display: "swap",
});

const labelClass =
  "text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400 font-[family-name:var(--font-landing-sans),ui-sans-serif,sans-serif]";

export default function SignupPage() {
  const router = useRouter();
  const loginStore = useAuthStore((s) => s.login);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await apiFetch<User>("/auth/signup", {
        method: "POST",
        json: { name, email, password },
      });
      const tokens = await apiFetch<{ access_token: string; refresh_token: string }>("/auth/login", {
        method: "POST",
        json: { email, password },
      });
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await apiFetch<User>("/auth/me");
      loginStore(tokens.access_token, tokens.refresh_token, me);
      toast.success("Account created");
      router.push("/dashboard");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className={cn(
        "landing-cyber-root landing-type-body relative isolate min-h-screen overflow-x-hidden bg-[radial-gradient(ellipse_120%_80%_at_50%_-20%,oklch(0.22_0.06_260)_0%,oklch(0.12_0.04_260)_42%,oklch(0.09_0.02_260)_100%)] px-4 py-10 sm:px-6",
        landingSans.variable,
      )}
    >
      <div className="landing-cyber-grid" aria-hidden />
      <div className="landing-cyber-scanlines" aria-hidden />

      <div className="relative z-[2] mx-auto flex w-full max-w-5xl flex-col gap-8">
        <header className="flex items-center justify-between gap-4">
          <Link
            href="/"
            className="inline-flex w-fit items-center gap-2 rounded-xl border border-white/[0.06] bg-card/30 px-3 py-2 ring-1 ring-cyan-500/15 backdrop-blur-md transition-colors hover:border-cyan-500/25 hover:bg-card/45"
          >
            <CyberGuardLockup variant="compact" />
          </Link>
          <Link
            href="/login"
            className="text-sm font-medium text-cyan-300/90 underline-offset-4 transition-colors hover:text-cyan-200 hover:underline"
          >
            Sign in
          </Link>
        </header>

        <div className="grid gap-6 lg:grid-cols-[1fr_1.05fr] lg:gap-8">
          <Card className="border-cyan-500/20 bg-black/35 shadow-[var(--landing-depth-1)] backdrop-blur-xl ring-1 ring-white/[0.04]">
            <CardHeader className="space-y-5 pb-2 sm:pb-4">
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-medium text-cyan-200">
                <Radar className="h-3.5 w-3.5 shrink-0" aria-hidden />
                Analyst workspace
              </div>
              <CardTitle
                className="font-[family-name:var(--font-display)] text-3xl font-bold leading-[1.15] tracking-[-0.03em] text-white sm:text-4xl"
              >
                Create your SOC console in one flow.
              </CardTitle>
              <CardDescription className="max-w-md text-sm leading-relaxed text-slate-300">
                Same stack as the open CyberGuard demo: real auth tokens, dashboard routes, and API
                hooks wired to your backend. No placeholder forms — this hits{" "}
                <code className="rounded bg-white/5 px-1 py-0.5 font-mono text-[11px] text-cyan-200/90">
                  /auth/signup
                </code>{" "}
                then signs you in.
              </CardDescription>
              <ul className="grid gap-2.5 pt-1 text-sm text-slate-200">
                <li className="flex items-start gap-2.5 rounded-lg border border-border/40 bg-card/25 px-3 py-2.5">
                  <UserPlus className="mt-0.5 h-4 w-4 shrink-0 text-cyan-300" aria-hidden />
                  <span>JWT session + Zustand store match the app shell you land in after signup.</span>
                </li>
                <li className="flex items-start gap-2.5 rounded-lg border border-border/40 bg-card/25 px-3 py-2.5">
                  <Plug className="mt-0.5 h-4 w-4 shrink-0 text-violet-300" aria-hidden />
                  <span>Bring your FastAPI on port 8000 or set NEXT_PUBLIC_API_URL for remote dev.</span>
                </li>
              </ul>
            </CardHeader>
          </Card>

          <Card className="border-border/50 bg-card/70 shadow-[var(--landing-depth-glow)] backdrop-blur-xl ring-1 ring-inset ring-white/[0.06]">
            <CardHeader className="space-y-1">
              <CardTitle className="font-[family-name:var(--font-display)] text-2xl font-semibold tracking-tight text-foreground">
                Create account
              </CardTitle>
              <CardDescription className="text-sm text-muted-foreground">
                Start monitoring in minutes — eight character minimum on the password.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={onSubmit} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="name" className={labelClass}>
                    Full name
                  </Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    autoComplete="name"
                    placeholder="Jordan Analyst"
                    className="h-11 border-border/60 bg-muted/15 font-[family-name:var(--font-landing-sans),ui-sans-serif,sans-serif] text-[15px] shadow-inner placeholder:text-muted-foreground/70"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email" className={labelClass}>
                    Work email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                    placeholder="you@org.com"
                    className="h-11 border-border/60 bg-muted/15 font-[family-name:var(--font-landing-sans),ui-sans-serif,sans-serif] text-[15px] shadow-inner placeholder:text-muted-foreground/70"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password" className={labelClass}>
                    Password
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                    autoComplete="new-password"
                    placeholder="At least 8 characters"
                    className="h-11 border-border/60 bg-muted/15 font-[family-name:var(--font-landing-sans),ui-sans-serif,sans-serif] text-[15px] shadow-inner placeholder:text-muted-foreground/70"
                  />
                </div>
                <Button
                  type="submit"
                  disabled={loading}
                  className={cn(
                    "h-11 w-full gap-2 text-base font-semibold shadow-lg transition-all",
                    "bg-gradient-to-r from-cyan-500 to-cyan-600 text-primary-foreground shadow-cyan-500/25 hover:from-cyan-400 hover:to-cyan-500",
                  )}
                >
                  {loading ? "Creating account…" : "Create account"}
                  {!loading && <ArrowRight className="h-4 w-4" aria-hidden />}
                </Button>
                <p className="text-center text-sm text-muted-foreground">
                  Already have an account?{" "}
                  <Link href="/login" className="font-medium text-cyan-400 hover:text-cyan-300 hover:underline">
                    Sign in
                  </Link>
                </p>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
