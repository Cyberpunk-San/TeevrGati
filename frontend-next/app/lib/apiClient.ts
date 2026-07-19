/**
 * apiClient.ts — centralized HTTP client for TeevrGati frontend
 *
 * Guarantees for every request:
 *  - Authorization: Bearer <token>
 *  - Content-Type: application/json  (for POST)
 *  - Accept: application/json
 *  - X-Request-ID: <uuid>            (for request tracing)
 *  - AbortController timeout         (default 30 s)
 *  - RFC 7807 error surface          (ApiError.detail, .status, .title)
 */

import { API_URL, API_KEY } from "../config";

// ── Types ─────────────────────────────────────────────────────────────────────
export class ApiError extends Error {
  status: number;
  title: string;
  detail: string;
  requestId: string | null;

  constructor(status: number, title: string, detail: string, requestId: string | null) {
    super(`[${status}] ${title}: ${detail}`);
    this.name = "ApiError";
    this.status = status;
    this.title = title;
    this.detail = detail;
    this.requestId = requestId;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function generateRequestId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}


async function parseError(res: Response, requestId: string | null): Promise<ApiError> {
  const contentType = res.headers.get("content-type") ?? "";
  let title = `HTTP ${res.status}`;
  let detail = res.statusText || "Unknown error";

  try {
    if (contentType.includes("problem+json") || contentType.includes("application/json")) {
      const body = await res.json();
      title = body.title ?? title;
      detail = body.detail ?? detail;
    } else {
      detail = (await res.text()) || detail;
    }
  } catch {
    // ignore JSON parse failure, use defaults
  }
  return new ApiError(res.status, title, detail, requestId);
}

// ── Core request ─────────────────────────────────────────────────────────────
interface RequestOptions {
  /** milliseconds before aborting (default 30 000) */
  timeoutMs?: number;
  signal?: AbortSignal;
}

export async function apiFetch<T = unknown>(
  path: string,
  init: RequestInit & RequestOptions = {}
): Promise<T> {
  const { timeoutMs = 30_000, signal: externalSignal, ...fetchInit } = init;

  // Merge abort signals
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const signal = externalSignal
    ? (AbortSignal as any).any?.([controller.signal, externalSignal]) ?? controller.signal
    : controller.signal;

  const url = `${API_URL}${path}`;
  const requestId = generateRequestId();

  const headers: Record<string, string> = {
    Accept: "application/json",
    Authorization: `Bearer ${API_KEY}`,
    "X-Request-ID": requestId,
    ...(fetchInit.body && !(fetchInit.body instanceof FormData)
      ? { "Content-Type": "application/json" }
      : {}),
    ...(fetchInit.headers as Record<string, string> | undefined),
  };

  try {
    const res = await fetch(url, { ...fetchInit, headers, signal });
    if (!res.ok) {
      throw await parseError(res, res.headers.get("X-Request-ID") ?? requestId);
    }
    // 204 No Content
    if (res.status === 204) return undefined as unknown as T;
    return (await res.json()) as T;
  } catch (err) {
    if ((err as Error).name === "AbortError") {
      throw new ApiError(408, "Request Timeout", `Request to ${path} timed out after ${timeoutMs}ms`, requestId);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

// ── Convenience wrappers ──────────────────────────────────────────────────────
export const apiGet = <T = unknown>(path: string, opts?: RequestOptions) =>
  apiFetch<T>(path, { method: "GET", ...opts });

export const apiPost = <T = unknown>(path: string, body: unknown, opts?: RequestOptions) =>
  apiFetch<T>(path, { method: "POST", body: JSON.stringify(body), ...opts });
