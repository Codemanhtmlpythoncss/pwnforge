// Minimal typed API client. Cookies carry the session; credentials included.

export interface User {
  id: number; username: string; display_name: string | null; role: string;
  email: string | null; xp: number; streak_days: number;
  preferred_specialization: string | null; must_change_password: boolean;
}

async function req<T = any>(method: string, path: string, body?: any): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    credentials: "include",
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new Error(data?.detail || `${res.status} ${res.statusText}`);
  }
  return data as T;
}

export const api = {
  get: <T = any>(p: string) => req<T>("GET", p),
  post: <T = any>(p: string, b?: any) => req<T>("POST", p, b),
  put: <T = any>(p: string, b?: any) => req<T>("PUT", p, b),
  del: <T = any>(p: string, b?: any) => req<T>("DELETE", p, b),
};

export function wsUrl(path: string): string {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  // In dev the vite proxy forwards ws; in prod same origin.
  const host = location.host;
  return `${proto}//${host}${path}`;
}

export const diffClass = (d: string) => `diff-chip d-${d}`;
