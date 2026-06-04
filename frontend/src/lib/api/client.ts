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
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/v1${path}`, {
      ...rest,
      headers,
      body: json !== undefined ? JSON.stringify(json) : rest.body,
    });
  } catch {
    throw new Error(
      `Cannot reach the API at ${API_BASE}. Start Docker Compose (api on port 8000) and set NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 in frontend/.env.local.`,
    );
  }
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
      const body = await res.json() as Record<string, unknown>;
      const detail = body.detail;
      if (typeof body.message === "string") msg = body.message;
      else if (typeof detail === "string") msg = detail;
      else if (detail && typeof detail === "object" && "message" in detail) {
        const m = (detail as { message?: unknown }).message;
        msg = typeof m === "string" ? m : JSON.stringify(detail);
      } else msg = JSON.stringify(body);
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

export async function downloadAlertsPortfolioPdf(filters: {
  severity?: string;
  status?: string;
}): Promise<void> {
  const t = getToken();
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (t) headers.Authorization = `Bearer ${t}`;

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/v1/alerts/generate-report`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        severity: filters.severity && filters.severity !== "all" ? filters.severity : null,
        status: filters.status && filters.status !== "all" ? filters.status : null,
        max_alerts: 500,
      }),
    });
  } catch {
    throw new Error(
      `Cannot reach the API at ${API_BASE}. Start Docker Compose (api on port 8000).`,
    );
  }

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
      const body = (await res.json()) as Record<string, unknown>;
      if (typeof body.detail === "string") msg = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }

  const blob = await res.blob();
  const stamp = new Date().toISOString().slice(0, 10);
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `cyberguard-alerts-${stamp}.pdf`;
  a.click();
  URL.revokeObjectURL(a.href);
}
