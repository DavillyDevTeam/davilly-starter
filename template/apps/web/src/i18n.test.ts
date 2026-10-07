import { describe, expect, it } from 'vitest';
import { i18n, initI18n } from './i18n';
import { supportedLocales } from './supportedLocales';

describe('i18n runtime', () => {
  it('resolves each generated locale without falling back', async () => {
    await initI18n();
    const titles: string[] = [];
    for (const lng of supportedLocales) {
      await i18n.changeLanguage(lng);
      expect(i18n.resolvedLanguage).toBe(lng);
      const title = i18n.t('landing.title');
      expect(title).not.toBe('landing.title');
      titles.push(title);
    }
    expect(new Set(titles).size).toBe(supportedLocales.length);
  });
});
