"use client";

import { create } from "zustand";

import { clearTokens, setTokens } from "@/lib/api/client";
import { queryClient } from "@/lib/query-client";
import type { User } from "@/lib/api/types";

interface AuthState {
  user: User | null;
  setUser: (u: User | null) => void;
  login: (access: string, refresh: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  login: (access, refresh, user) => {
    queryClient.clear();
    setTokens(access, refresh);
    set({ user });
  },
  logout: () => {
    queryClient.clear();
    clearTokens();
    set({ user: null });
  },
}));
