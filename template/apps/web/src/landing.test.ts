import { describe, expect, it } from 'vitest';
import { defaultLocale, projectName, supportedLocales } from './supportedLocales';

const catalogs = import.meta.glob('../../../locales/*/common.json', {
  eager: true,
  import: 'default',
});

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function landingOf(catalog: unknown): Record<string, unknown> | undefined {
  if (!isRecord(catalog)) {
    return undefined;
  }
  const landing = catalog['landing'];
  return isRecord(landing) ? landing : undefined;
}

describe('landing catalogs', () => {
  it('ships a complete default language', () => {
    expect(supportedLocales.includes(defaultLocale)).toBe(true);
    expect(projectName).toBeTruthy();
    const catalogPath = Object.keys(catalogs).find((path) =>
      path.endsWith(`/locales/${defaultLocale}/common.json`),
    );
    expect(catalogPath).toBeDefined();
    if (catalogPath === undefined) {
      return;
    }
    const landing = landingOf(catalogs[catalogPath]);
    expect(landing).toBeDefined();
    if (landing === undefined) {
      return;
    }
    expect(typeof landing['title']).toBe('string');
    expect(typeof landing['cta']).toBe('string');
    const features = landing['features'];
    expect(isRecord(features)).toBe(true);
    if (isRecord(features)) {
      expect(typeof features['path']).toBe('string');
      expect(typeof features['day']).toBe('string');
      expect(typeof features['grow']).toBe('string');
    }
  });
});
