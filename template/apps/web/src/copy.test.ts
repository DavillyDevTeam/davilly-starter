import { describe, expect, it } from 'vitest';
import { copy, defaultLocale, projectName } from './copy';
describe('landing catalogs', () => {
  it('ships a complete default language', () => {
    expect(copy[defaultLocale]?.title).toBeTruthy();
    expect(projectName).toBeTruthy();
    for (const catalog of Object.values(copy)) {
      expect(catalog.features).toHaveLength(3);
      expect(catalog.cta).toBeTruthy();
    }
  });
});
