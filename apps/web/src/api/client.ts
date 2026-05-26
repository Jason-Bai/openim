const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export type ApiResponse<T> =
  | { request_id: string; ok: true; data: T }
  | {
      request_id: string;
      ok: false;
      error: { code: string; message: string; retryable: boolean };
    };

export class ApiError extends Error {
  code: string;
  retryable: boolean;

  constructor(code: string, message: string, retryable: boolean) {
    super(message);
    this.code = code;
    this.retryable = retryable;
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  });
  const body = (await response.json()) as ApiResponse<T>;
  if (!body.ok) {
    throw new ApiError(body.error.code, body.error.message, body.error.retryable);
  }
  return body.data;
}

