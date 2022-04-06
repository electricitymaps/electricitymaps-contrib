// Production/imports-exports mode
const modeColor = {
  solar: '#f27406',
  wind: '#74cdb9',
  hydro: '#2772b2',
  'hydro storage': '#0052cc',
  battery: 'lightgray',
  'battery storage': '#b76bcf',
  biomass: '#166a57',
  geothermal: 'yellow',
  nuclear: '#AEB800',
  gas: '#bb2f51',
  coal: '#ac8c35',
  oil: '#867d66',
  unknown: '#ACACAC',
};
const modeOrder = [
  'nuclear',
  'geothermal',
  'biomass',
  'coal',
  'wind',
  'solar',
  'hydro',
  'hydro storage',
  'battery storage',
  'gas',
  'oil',
  'unknown',
];
const PRODUCTION_MODES = modeOrder.filter(d => d.indexOf('storage') === -1);
const STORAGE_MODES = modeOrder.filter(d => d.indexOf('storage') !== -1).map(d => d.replace(' storage', ''));

const DEFAULT_FLAG_SIZE = 16;

const DATA_FETCH_INTERVAL = 5 * 60 * 1000; // 5 minutes

const LANGUAGE_NAMES = {
  "ar": "اللغة العربية الفصحى",
  "cs": "Čeština",
  "da": "Dansk",
  "de": "Deutsch",
  "el": "Ελληνικά",
  "en": "English",
  "es": "Español",
  "et": "Eesti",
  "fi": "Suomi",
  "fr": "Français",
  "hr": "Hrvatski",
  "id": "Bahasa Indonesia",
  "it": "Italiano",
  "ja": "日本語",
  "ko": "한국어",
  "nl": "Nederlands",
  "no-nb": "Norsk (bokmål)",
  "pl": "Polski",
  "pt-br": "Português (Brasileiro)",
  "ro": "Română",
  "ru": "Русский язык",
  "sk": "Slovenčina",
  "sv": "Svenska",
  "vi": "Tiếng Việt",
  "zh-cn": "中文 (Mainland China)",
  "zh-hk": "中文 (Hong Kong)",
  "zh-tw": "中文 (Taiwan)"
}

export {
  modeColor,
  modeOrder,
  PRODUCTION_MODES,
  STORAGE_MODES,
  DEFAULT_FLAG_SIZE,
  DATA_FETCH_INTERVAL,
  LANGUAGE_NAMES,
};
