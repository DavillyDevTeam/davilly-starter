import i18n from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import type { Resource, ResourceKey, ResourceLanguage } from 'i18next';
import { initReactI18next } from 'react-i18next';
import { defaultLocale, supportedLocales } from './supportedLocales';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function asResourceKey(value: unknown): ResourceKey | undefined {
  if (typeof value === 'string' || isRecord(value)) {
    return value;
  }
  return undefined;
}

const catalogModules = import.meta.glob('../../../locales/*/*.json', {
  eager: true,
  import: 'default',
});

function loadResources(): Resource {
  const resources: Resource = {};
  for (const [path, catalog] of Object.entries(catalogModules)) {
    const parts = /\/locales\/([^/]+)\/([^/]+)\.json$/.exec(path);
    const resourceKey = asResourceKey(catalog);
    if (parts === null || resourceKey === undefined) {
      continue;
    }
    const locale = parts[1];
    const namespace = parts[2];
    if (locale === undefined || namespace === undefined) {
      continue;
    }
    const language: ResourceLanguage = resources[locale] ?? {};
    language[namespace] = resourceKey;
    resources[locale] = language;
  }
  return resources;
}

function readNested(value: unknown, path: readonly string[]): unknown {
  let current: unknown = value;
  for (const part of path) {
    if (!isRecord(current)) {
      return undefined;
    }
    current = current[part];
  }
  return current;
}

export function languageLabel(lng: string): string {
  const path = Object.keys(catalogModules).find((candidate) =>
    candidate.endsWith(`/locales/${lng}/common.json`),
  );
  if (path === undefined) {
    return lng;
  }
  const label = readNested(catalogModules[path], ['language', 'label']);
  return typeof label === 'string' ? label : lng;
}

function syncDocumentLang(lng: string): void {
  if (typeof document === 'undefined') {
    return;
  }
  document.documentElement.lang = lng;
}

export { i18n };

export async function initI18n(): Promise<void> {
  if (!i18n.isInitialized) {
    await i18n.use(LanguageDetector).use(initReactI18next).init({
      resources: loadResources(),
      fallbackLng: defaultLocale,
      supportedLngs: [...supportedLocales],
      ns: ['common', 'errors'],
      defaultNS: 'common',
      interpolation: { escapeValue: false },
      load: 'currentOnly',
      react: { useSuspense: false },
    });
    i18n.on('languageChanged', (lng: string) => {
      syncDocumentLang(lng);
    });
  }
  syncDocumentLang(i18n.resolvedLanguage ?? defaultLocale);
}
