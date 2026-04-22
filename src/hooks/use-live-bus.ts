"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { API_BASE } from "@/lib/constants";

function toWsUrl(httpBase: string): string {
  if (httpBase.startsWith("https")) return httpBase.replace(/^https/, "wss");
  return httpBase.replace(/^http/, "ws");
}

export function useLiveBus(enabled: boolean) {
  const qc = useQueryClient();
  const ref = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled || typeof window === "undefined") return;
    const token = localStorage.getItem("cg_access_token");
    if (!token) return;
    const url = `${toWsUrl(API_BASE)}/api/v1/ws?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    ref.current = ws;
    ws.onmessage = () => {
      qc.invalidateQueries({ queryKey: ["alerts"] });
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
      qc.invalidateQueries({ queryKey: ["dashboard-charts"] });
      qc.invalidateQueries({ queryKey: ["incidents"] });
      qc.invalidateQueries({ queryKey: ["events"] });
    };
    ws.onerror = () => {
      /* silent — demo-friendly */
    };
    return () => {
      ws.close();
      ref.current = null;
    };
  }, [enabled, qc]);
}
