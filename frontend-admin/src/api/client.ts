const TOKEN_KEY = "mfc.admin.token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

/** Decode JWT payload (no signature check — backend is the source of truth). */
export function decodeJwtPayload(token: string | null): Record<string, unknown> | null {
  if (!token) return null;
  try {
    const part = token.split(".")[1];
    if (!part) return null;
    const padded = part.replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
}

export function getCurrentAdminId(): number | null {
  const payload = decodeJwtPayload(getToken());
  const v = payload?.["admin_id"];
  return typeof v === "number" ? v : null;
}

export interface ApiError extends Error {
  status: number;
  code?: string;
  detail?: unknown;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${import.meta.env.VITE_API_URL}/api${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: "include",
  });

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const err = new Error(
      (data?.error?.message ?? data?.detail ?? `HTTP ${res.status}`) as string,
    ) as ApiError;
    err.status = res.status;
    err.code = data?.error?.code;
    err.detail = data;
    throw err;
  }
  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
  del: <T>(path: string) => request<T>("DELETE", path),
};
