import moment from 'moment';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import HttpApi from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';
import { isProduction } from './environment';
//import LanguageDetector from 'i18next-browser-languagedetector';
import { history } from './router';

// TODO: Get rid of this when a better system is put in place for switching languages.
// See https://github.com/tmrowco/electricitymap-contrib/issues/2382.
function hideLanguageSearchParam() {
  const searchParams = new URLSearchParams(history.location.search);
  searchParams.delete('lang');
  history.replace(`?${searchParams.toString()}`);
}

// Init localisation package
i18n
  .use(HttpApi)
  // detect user language
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    debug: isProduction() ? false : true,
    backend: {
      loadPath: 'locales/{{lng}}.json',
      crossDomain: true
    },
    detection: {
      order: ['querystring', 'cookie', 'localStorage', 'sessionStorage', 'navigator', 'htmlTag'],
      lookupQuerystring: 'lang',
      caches: ['localStorage', 'cookie'],
    },
    interpolation: {
      escapeValue: false, // not needed for react as it escapes by default
    },
  }).then(() => {
    hideLanguageSearchParam();
  });

i18n.on('languageChanged', function(lng) {
  moment.locale(lng);
  document.documentElement.setAttribute('lang', lng);
});

export default i18n;
