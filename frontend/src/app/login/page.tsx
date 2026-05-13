"use client";

import { DM_Sans, Syne } from "next/font/google";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { ArrowRight, Shield, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch, setTokens } from "@/lib/api/client";
import type { User } from "@/lib/api/types";
import { useAuthStore } from "@/store/auth-store";

const displayFont = Syne({ subsets: ["latin"], weight: ["600", "700"] });
const bodyFont = DM_Sans({ subsets: ["latin"], weight: ["400", "500", "700"] });

export default function LoginPage() {
  const router = useRouter();
  const loginStore = useAuthStore((s) => s.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const tokens = await apiFetch<{ access_token: string; refresh_token: string }>("/auth/login", {
        method: "POST",
        json: { email, password },
      });
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await apiFetch<User>("/auth/me");
      loginStore(tokens.access_token, tokens.refresh_token, me);
      toast.success("Welcome back");
      router.push("/dashboard");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className={`${bodyFont.className} relative flex min-h-screen items-center justify-center overflow-hidden bg-[#0a0a0f] px-4 py-8`}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(34,211,238,0.2),transparent_40%),radial-gradient(circle_at_80%_15%,rgba(139,92,246,0.18),transparent_35%),radial-gradient(circle_at_50%_80%,rgba(34,197,94,0.12),transparent_35%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-40 [background:linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] [background-size:24px_24px]" />
      <div className="relative grid w-full max-w-5xl gap-4 lg:grid-cols-2">
        <Card className="border-cyan-500/20 bg-black/30 backdrop-blur-xl">
          <CardHeader className="space-y-4">
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-300">
              <Shield className="h-3.5 w-3.5" />
              Trusted SOC Workspace
            </div>
            <CardTitle
              className={`${displayFont.className} text-4xl leading-tight tracking-[-0.03em] text-white`}
            >
              Command your defense posture with confidence.
            </CardTitle>
            <CardDescription className="max-w-md text-sm leading-relaxed text-slate-300">
              CyberGuard AI unifies alerts, incidents, threat intelligence, and training labs in a
              single operator-grade cockpit.
            </CardDescription>
            <div className="grid gap-2 pt-2 text-sm">
              <div className="flex items-center gap-2 rounded-md border border-border/50 bg-card/30 px-3 py-2 text-slate-200">
                <Sparkles className="h-4 w-4 text-cyan-300" />
                AI-guided incident analysis with MITRE mapping
              </div>
              <div className="flex items-center gap-2 rounded-md border border-border/50 bg-card/30 px-3 py-2 text-slate-200">
                <Sparkles className="h-4 w-4 text-violet-300" />
                Live attack simulation and learning-grade scoring
              </div>
            </div>
          </CardHeader>
        </Card>
        <Card className="border-border/60 bg-card/80 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className={`${displayFont.className} text-2xl tracking-tight`}>Sign in</CardTitle>
            <CardDescription>Access your SOC console and continue your workflows.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="h-11 bg-muted/20"
                  placeholder="analyst@cyberguard.ai"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="h-11 bg-muted/20"
                  placeholder="Enter your password"
                />
              </div>
              <Button type="submit" className="h-11 w-full gap-2" disabled={loading}>
                {loading ? "Signing in…" : "Sign in"}
                {!loading && <ArrowRight className="h-4 w-4" />}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                No account?{" "}
                <Link href="/signup" className="text-cyan-400 hover:underline">
                  Sign up
                </Link>
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
