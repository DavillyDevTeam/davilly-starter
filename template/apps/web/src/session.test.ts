import { describe, expect, it } from 'vitest';
import { oauthError, readAccessToken } from './session';

describe('access token fragment', () => {
  it('reads a bearer token and ignores anything else', () => {
    expect(readAccessToken('#access_token=abc.def')).toBe('abc.def');
    expect(readAccessToken('')).toBeNull();
    expect(readAccessToken('#other=1')).toBeNull();
    expect(readAccessToken('#access_token=')).toBeNull();
  });

  it('accepts only known provider errors', () => {
    expect(oauthError('?error=oauth_failed')).toBe('oauth_failed');
    expect(oauthError('?error=oauth_account_exists')).toBe('oauth_account_exists');
    expect(oauthError('?error=<script>')).toBeNull();
    expect(oauthError('')).toBeNull();
  });
});
