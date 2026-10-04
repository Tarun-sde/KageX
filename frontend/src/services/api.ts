const baseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export interface Health {
  status: 'ok';
  service: 'kagex-api';
  version: string;
}

export interface Readiness {
  status: 'ready' | 'unavailable';
  postgres: boolean;
  redis: boolean;
}

async function request(path: string, signal: AbortSignal): Promise<Response> {
  return fetch(`${baseUrl}${path}`, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(10000)]),
    headers: { Accept: 'application/json' },
  });
}

export async function getHealth(signal: AbortSignal): Promise<Health> {
  const response = await request('/health', signal);
  const data: unknown = await response.json();
  if (
    !response.ok ||
    !data ||
    typeof data !== 'object' ||
    !('status' in data) ||
    data.status !== 'ok' ||
    !('service' in data) ||
    data.service !== 'kagex-api' ||
    !('version' in data) ||
    typeof data.version !== 'string'
  ) {
    throw new Error('Backend health unavailable');
  }
  return data as Health;
}

export async function getReadiness(signal: AbortSignal): Promise<Readiness> {
  const response = await request('/ready', signal);
  const data: unknown = await response.json();
  if (
    ![200, 503].includes(response.status) ||
    !data ||
    typeof data !== 'object' ||
    !('status' in data) ||
    !['ready', 'unavailable'].includes(String(data.status)) ||
    !('postgres' in data) ||
    typeof data.postgres !== 'boolean' ||
    !('redis' in data) ||
    typeof data.redis !== 'boolean' ||
    (data.status === 'ready') !== (data.postgres && data.redis) ||
    (response.status === 200) !== (data.status === 'ready')
  ) {
    throw new Error('Dependency status unavailable');
  }
  return data as Readiness;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

export async function apiRequest(
  path: string,
  init: RequestInit = {},
): Promise<unknown> {
  const response = await fetch(`${baseUrl}/api/v1${path}`, {
    ...init,
    credentials: 'include',
    signal: init.signal
      ? AbortSignal.any([init.signal, AbortSignal.timeout(130000)])
      : AbortSignal.timeout(130000),
    headers: {
      Accept: 'application/json',
      'X-KageX-Request': '1',
      ...(typeof init.body === 'string'
        ? { 'Content-Type': 'application/json' }
        : {}),
      ...init.headers,
    },
  });
  if (response.status === 204) return null;
  const data: unknown = await response.json();
  if (!response.ok) {
    if (response.status === 401)
      window.dispatchEvent(new Event('kagex:unauthenticated'));
    let code = 'REQUEST_FAILED';
    let message = 'The request failed. Please try again.';
    if (
      data &&
      typeof data === 'object' &&
      'error' in data &&
      data.error &&
      typeof data.error === 'object'
    ) {
      if ('code' in data.error && typeof data.error.code === 'string')
        code = data.error.code;
      if ('message' in data.error && typeof data.error.message === 'string')
        message = data.error.message;
    }
    throw new ApiError(response.status, code, message);
  }
  return data;
}

export function errorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : 'Connection failed. Please try again.';
}
