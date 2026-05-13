"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useLiveBus } from "@/hooks/use-live-bus";
import { apiFetch } from "@/lib/api/client";
import type { User } from "@/lib/api/types";
import { useAuthStore } from "@/store/auth-store";

import { AppHeader } from "./app-header";
import { AppSidebar } from "./app-sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, setUser, logout } = useAuthStore();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await apiFetch<User>("/auth/me");
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) {
          logout();
          router.replace("/login");
        }
      } finally {
        if (!cancelled) setReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router, setUser, logout]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!user) return null;

  return <AppShellInner>{children}</AppShellInner>;
}

function AppShellInner({ children }: { children: React.ReactNode }) {
  useLiveBus(true);
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <AppSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <AppHeader />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  );
}

