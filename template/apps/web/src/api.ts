export interface Providers {
  google: boolean;
  github: boolean;
}

export type Me =
  | { status: 'ok'; email: string }
  | { status: 'anonymous' }
  | { status: 'error' };

export function apiUrl(
  path: string,
  base: string = import.meta.env.VITE_API_URL ?? '',
): string {
  return `${base.replace(/\/+$/, '')}${path}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (text === '') return null;
  return parseJson(text);
}

function parseJson(text: string): unknown {
  const value: unknown = JSON.parse(text);
  return value;
}

export async function fetchProviders(signal: AbortSignal): Promise<Providers | null> {
  try {
    const response = await fetch(apiUrl('/auth/providers'), { signal });
    if (!response.ok) return null;
    const body = await readJson(response);
    if (!isRecord(body)) return null;
    const google = body['google'];
    const github = body['github'];
    if (typeof google !== 'boolean' || typeof github !== 'boolean') return null;
    return { google, github };
  } catch {
    return null;
  }
}

export async function registerAccount(
  email: string,
  password: string,
): Promise<boolean> {
  try {
    const response = await fetch(apiUrl('/auth/register'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return response.status === 201;
  } catch {
    return false;
  }
}

export async function login(email: string, password: string): Promise<string | null> {
  try {
    const response = await fetch(apiUrl('/auth/jwt/login'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
    });
    if (!response.ok) return null;
    const body = await readJson(response);
    if (!isRecord(body)) return null;
    const token = body['access_token'];
    if (typeof token !== 'string' || token === '') return null;
    return token;
  } catch {
    return null;
  }
}

export async function fetchMe(token: string, signal: AbortSignal): Promise<Me> {
  try {
    const response = await fetch(apiUrl('/users/me'), {
      signal,
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.status === 401) return { status: 'anonymous' };
    if (!response.ok) return { status: 'error' };
    const body = await readJson(response);
    if (!isRecord(body) || typeof body['email'] !== 'string') return { status: 'error' };
    return { status: 'ok', email: body['email'] };
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      return { status: 'error' };
    }
    return { status: 'error' };
  }
}

export async function logout(token: string): Promise<void> {
  try {
    await fetch(apiUrl('/auth/jwt/logout'), {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    // The JWT is dropped locally either way.
  }
}
