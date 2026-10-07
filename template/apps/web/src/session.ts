let accessToken: string | null = null;

export function readAccessToken(hash: string): string | null {
  const source = hash.startsWith('#') ? hash.slice(1) : hash;
  if (source === '') return null;
  const token = new URLSearchParams(source).get('access_token');
  if (token === null || token === '') return null;
  return token;
}

export function oauthError(search: string): string | null {
  const value = new URLSearchParams(search).get('error');
  if (
    value === 'oauth_failed' ||
    value === 'oauth_account_exists' ||
    value === 'oauth_invalid_state'
  ) {
    return value;
  }
  return null;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function captureHashToken(): void {
  const token = readAccessToken(window.location.hash);
  if (token === null) return;
  setAccessToken(token);
  const next = `${window.location.pathname}${window.location.search}`;
  window.history.replaceState(null, '', next);
}
