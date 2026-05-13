import { API_BASE } from "@/lib/constants";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("cg_access_token");
}

export function setTokens(access: string, refresh?: string) {
  localStorage.setItem("cg_access_token", access);
  if (refresh) localStorage.setItem("cg_refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("cg_access_token");
  localStorage.removeItem("cg_refresh_token");
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const { json, headers: hdrs, ...rest } = init;
  const headers = new Headers(hdrs);
  if (json !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  const t = getToken();
  if (t) headers.set("Authorization", `Bearer ${t}`);
  const res = await fetch(`${API_BASE}/api/v1${path}`, {
    ...rest,
    headers,
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  });
  if (res.status === 401) {
    clearTokens();
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const body = await res.json();
      msg = body.message || body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(typeof msg === "string" ? msg : "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export function downloadReport(reportId: number) {
  const t = getToken();
  const url = `${API_BASE}/api/v1/reports/${reportId}/download`;
  const a = document.createElement("a");
  a.href = url;
  a.download = `report-${reportId}.pdf`;
  fetch(url, { headers: { Authorization: `Bearer ${t}` } })
    .then((r) => r.blob())
    .then((blob) => {
      a.href = URL.createObjectURL(blob);
      a.click();
      URL.revokeObjectURL(a.href);
    });
}
