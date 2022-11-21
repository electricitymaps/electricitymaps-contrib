import i18n from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import HttpApi from 'i18next-http-backend';
import { initReactI18next } from 'react-i18next';

// eslint-disable-next-line no-constant-condition
const LOCALES_PATH = 'window.isCordova' ? 'locales' : '/locales'; // TODO test on mobile

const LOCALE_TO_FACEBOOK_LOCALE: { [key: string]: string } = {
  ar: 'ar_AR',
  cs: 'cs_CZ',
  da: 'da_DK',
  de: 'de_DE',
  el: 'el_GR',
  en: 'en_US',
  es: 'es_ES',
  et: 'et_EE',
  fi: 'fi_FI',
  fr: 'fr_FR',
  hr: 'hr_HR',
  id: 'id_ID',
  it: 'it_IT',
  ja: 'ja_JP',
  ko: 'ko_KR',
  nl: 'nl_NL',
  no: 'no_NB',
  'no-NB': 'no_NB',
  pl: 'pl_PL',
  'pt-BR': 'pt_BR',
  ro: 'ro_RO',
  ru: 'ru_RU',
  sk: 'sk_SK',
  sv: 'sv_SE',
  vn: 'vi_VN',
  'zh-cn': 'zh_CN',
  'zh-hk': 'zh_HK',
  'zh-tw': 'zh_TW',
};

// Init localisation package and ensure it uses relevant plugins
// eslint-disable-next-line import/no-named-as-default-member
i18n
  .use(HttpApi)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    debug: import.meta.env.DEV,
    backend: {
      loadPath: `/${LOCALES_PATH}/{{lng}}.json`,
      crossDomain: true,
      // request: requestWithXmlHttpRequest, // TODO: test on mobile, if issue check out [INSERT PR]
    },
    detection: {
      order: ['querystring', 'localStorage', 'sessionStorage', 'navigator', 'htmlTag'],
      lookupQuerystring: 'lang',
      caches: ['localStorage'],
    },
    interpolation: {
      escapeValue: false, // Not needed for react as it escapes by default
    },
  });

i18n.on('languageChanged', function (lng) {
  document.documentElement.setAttribute('lang', lng);
  // TODO: Use react-helmet to manage meta tags
  document.title = `Electricity Maps | ${i18n.t('misc.maintitle')}`;
  // Optional chaining added to ensure jsdom works
  document
    .querySelector('meta[property="og:locale"]')
    ?.setAttribute('content', LOCALE_TO_FACEBOOK_LOCALE[lng]);
});

export { default } from 'i18next';
