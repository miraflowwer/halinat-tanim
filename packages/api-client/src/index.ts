import { apiBaseUrl } from "@tanim/config";

type ApiRequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

export class ApiClientError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
  }
}

let csrfToken: string | null = null;

export function setCsrfToken(value: string | null) {
  csrfToken = value;
}

export function getCsrfToken() {
  return csrfToken;
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  if (csrfToken && options.method && !["GET", "HEAD"].includes(options.method.toUpperCase())) {
    headers.set("X-CSRF-Token", csrfToken);
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    credentials: "include",
    headers,
  });
  const payload = (await response.json().catch(() => ({}))) as Record<string, unknown>;

  if (!response.ok) {
    const detail = payload.detail;
    const error =
      typeof detail === "object" && detail !== null
        ? (detail as Record<string, unknown>)
        : {};
    const code = typeof error.code === "string" ? error.code : "REQUEST_FAILED";
    const message = typeof error.message === "string" ? error.message : "The request failed.";
    throw new ApiClientError(code, message, response.status);
  }

  if (typeof payload.csrf_token === "string") {
    setCsrfToken(payload.csrf_token);
  }
  if (payload.authenticated === false) {
    setCsrfToken(null);
  }
  return payload as T;
}
