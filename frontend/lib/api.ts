/**
 * Typed fetch wrapper for the MusicMatch API — the same contract a mobile client uses.
 * Tokens live in memory/localStorage and travel ONLY in the Authorization header,
 * never in query strings (roadmap Phase 5).
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem("mm_token", token);
  else localStorage.removeItem("mm_token");
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("mm_token");
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, String(body.detail));
  }
  return (await res.json()) as T;
}
