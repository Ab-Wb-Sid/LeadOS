const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

// Mirrors backend/app/schemas/user.py UserRead
export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface LogoutResponse {
  message: string;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

// FastAPI error bodies are either { detail: string } (e.g. 401 from auth.py)
// or { detail: [{ loc, msg, type }, ...] } (422 pydantic validation errors).
interface FastApiErrorBody {
  detail?: string | { loc: (string | number)[]; msg: string; type: string }[];
}

function extractErrorMessage(body: unknown): string | null {
  if (!body || typeof body !== 'object' || !('detail' in body)) return null;
  const { detail } = body as FastApiErrorBody;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((e) => e.msg).join('; ');
  }
  return null;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      // Required so the httpOnly access_token cookie set by /auth/login
      // is sent on every subsequent request, and so Set-Cookie from the
      // backend is honored by the browser.
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError(0, 'Could not reach the server. Check your connection and try again.');
  }

  if (!response.ok) {
    let message = response.statusText || `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      message = extractErrorMessage(body) ?? message;
    } catch {
      // No JSON body on this error response — fall back to statusText.
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

/** POST /auth/login — sets the httpOnly JWT cookie, returns the logged-in user. */
export function login(email: string, password: string): Promise<User> {
  return request<User>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

/** POST /auth/logout — clears the cookie. */
export function logout(): Promise<LogoutResponse> {
  return request<LogoutResponse>('/auth/logout', {
    method: 'POST',
  });
}

/** GET /auth/me — resolves the current user from the cookie, or throws ApiError(401, ...). */
export function getMe(): Promise<User> {
  return request<User>('/auth/me', {
    method: 'GET',
  });
}
