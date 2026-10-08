import { describe, expect, it, vi } from 'vitest';
import { apiUrl } from './api';
describe('apiUrl', () => {
  it('uses a relative /api path when the Pages origin is unset', () => {
    vi.stubEnv('VITE_API_URL', '');
    try {
      expect(apiUrl('/api/health', '')).toBe('/api/health');
      expect(apiUrl('/api/health')).toBe('/api/health');
    } finally {
      vi.unstubAllEnvs();
    }
  });
  it('prefixes the build-time API origin', () => {
    expect(apiUrl('/api/health', 'https://api.example.com')).toBe(
      'https://api.example.com/api/health',
    );
  });
  it('strips a trailing slash from the origin', () => {
    expect(apiUrl('/api/health', 'https://api.example.com/')).toBe(
      'https://api.example.com/api/health',
    );
  });
});
