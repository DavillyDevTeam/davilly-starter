import { useTranslation } from 'react-i18next';
import { languageLabel } from './i18n';
import { supportedLocales } from './supportedLocales';

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation('common');
  const current = i18n.resolvedLanguage ?? i18n.language;
  return (
    <nav aria-label={t('nav.language')}>
      {supportedLocales.map((lng) => (
        <button
          key={lng}
          type="button"
          aria-pressed={current === lng}
          onClick={() => {
            void i18n.changeLanguage(lng);
          }}
        >
          {languageLabel(lng)}
        </button>
      ))}
    </nav>
  );
}
