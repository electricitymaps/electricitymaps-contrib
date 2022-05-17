import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import HttpApi from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';
import { isProduction } from './environment';
import { LOCALE_TO_FACEBOOK_LOCALE } from './constants';
import { history } from './router';

const LOCALES_PATH = window.isCordova ? 'locales' : '/locales';

function hideLanguageSearchParam() {
  const searchParams = new URLSearchParams(history.location.search);
  searchParams.delete('lang');
  history.replace(`?${searchParams.toString()}`);
}

// This function is copied and slightly adjusted from https://github.com/i18next/i18next-http-backend/blob/master/lib/request.js
// The changes are done in order to make it work cross-platform
// See source for these changes: https://github.com/i18next/i18next-http-backend/issues/23#issuecomment-718929822
function requestWithXmlHttpRequest(options, url, payload, callback) {
  try {
    const x = new XMLHttpRequest();
    x.open('GET', url, 1);
    if (!options.crossDomain) {
      x.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    }
    x.withCredentials = Boolean(options.withCredentials);
    if (payload) {
      x.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    }
    if (x.overrideMimeType) {
      x.overrideMimeType('application/json');
    }
    let h = options.customHeaders;
    h = typeof h === 'function' ? h() : h;
    if (h) {
      for (var i in h) {
        x.setRequestHeader(i, h[i]);
      }
    }
    x.onreadystatechange = () => {
      x.readyState > 3 &&
        callback(x.status >= 400 ? x.statusText : null, {
          status: x.status || 200,
          data: x.responseText,
        }); // in android webview loading a file is status status 0
    };
    x.send(payload);
  } catch (e) {
    console && console.error(e);
  }
}

// Init localisation package and ensure it uses relevant plugins
i18n
  .use(HttpApi)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    debug: isProduction() ? false : true,
    backend: {
      loadPath: `${LOCALES_PATH}/{{lng}}.json`,
      crossDomain: true,
      request: requestWithXmlHttpRequest,
    },
    detection: {
      order: ['querystring', 'localStorage', 'sessionStorage', 'navigator', 'htmlTag'],
      lookupQuerystring: 'lang',
      caches: ['localStorage'],
    },
    interpolation: {
      escapeValue: false, // not needed for react as it escapes by default
    },
  })
  .then(() => {
    hideLanguageSearchParam();
  });

i18n.on('languageChanged', function (lng) {
  document.documentElement.setAttribute('lang', lng);
  // TODO: Use react-helmet to manage meta tags
  document.title = `electricityMap | ${i18n.t('misc.maintitle')}`;
  document.querySelector('meta[property="og:locale"]').setAttribute('content', LOCALE_TO_FACEBOOK_LOCALE[lng]);
});

export default i18n;
