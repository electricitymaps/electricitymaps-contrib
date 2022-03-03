import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import HttpApi from 'i18next-http-backend';
import { isProduction } from './environment';
//import LanguageDetector from 'i18next-browser-languagedetector';

// Init localisation package
await i18n
  .use(HttpApi)
  // detect user language
  // .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    debug: isProduction() ? false : true,

    backend: {
      loadPath: '/locales/{{lng}}.json',
    },

    interpolation: {
      escapeValue: false, // not needed for react as it escapes by default
    },
  });

export default i18n;
