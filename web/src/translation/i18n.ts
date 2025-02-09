import { setTag } from '@sentry/react';
import i18n from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import resourcesToBackend from 'i18next-resources-to-backend';
import { initReactI18next } from 'react-i18next';
import { localeToFacebookLocale } from 'translation/locales';

// Regular expression for valid language or locale strings
const VALID_LOCALE_REGEX = /^[A-Za-z]{2}(-[A-Za-z]{2})?$/;

const LOCALE_CLEANUP_PATTERN = /[^A-Za-z-]/g;

export const sanitizeLocale = (locale: string): string => {
  // Get the first 5 characters and strip all non-alphabetic characters except hyphens from the locale string
  locale = locale.slice(0, 5).replaceAll(LOCALE_CLEANUP_PATTERN, '');

  if (VALID_LOCALE_REGEX.test(locale)) {
    return Intl.getCanonicalLocales(locale)[0];
  }

  console.warn(
    `Invalid locale string: ${locale}, could not sanitize, defaulting to 'en'`
  );
  return 'en';
};

// Init localisation package and ensure it uses relevant plugins
// eslint-disable-next-line import/no-named-as-default-member
i18n
  .use(resourcesToBackend((language: string) => import(`../locales/${language}.json`)))
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    detection: {
      order: ['querystring', 'localStorage', 'sessionStorage', 'navigator', 'htmlTag'],
      lookupQuerystring: 'lang',
      caches: ['localStorage'],
      convertDetectedLanguage: sanitizeLocale,
    },
    interpolation: {
      escapeValue: false, // Not needed for react as it escapes by default
    },
  });

i18n.on('languageChanged', (lng: keyof typeof localeToFacebookLocale) => {
  setTag('app.locale', lng);
});

export { default } from 'i18next';
