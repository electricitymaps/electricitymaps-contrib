require('colors');

const flatMap = require('lodash.flatmap');

const { languageNames } = require('./locales-config.json');

function getAndPrintOutput() {
  const locales = Object.keys(languageNames);
  const result = locales.map(translationStatusFor).concat().sort((a, b) => a.translated - b.translated).reverse().map(toText);

  console.log('\nTranslation status for all languages\n'.underline.bold);
  result.forEach((res) => console.log(res));
}

// Gets all deepest level keys from a JSON (they stand for concrete translated terms)
function getDeepKeysFromJSON(data, prefix = '') {
  if (typeof data === 'string') return [prefix];
  return flatMap(data, (d, i) => getDeepKeysFromJSON(d, `${prefix}___${i}`));
}

function getTermsForLanguage(language) {
  return getDeepKeysFromJSON(require(`./public/locales/${language}.json`));
}

function getTranslationProgressColor(translated) {
  if (translated > 0.9) return 'green';
  if (translated > 0.7) return 'yellow';
  if (translated > 0.5) return 'magenta';
  return 'red';
}

const difference = (a, b) => a.filter(c => !b.includes(c))

function translationStatusFor(language) {
  const totalWords = getTermsForLanguage('en'); // the default language in locale settings
  const translatedWords = getTermsForLanguage(language);
  const untranslatedWords = [totalWords, translatedWords].reduce(difference);
  const legacyTerms = [translatedWords, totalWords].reduce(difference);
  const translated = 1 - [...untranslatedWords].length / [...totalWords].length;
  const percentageString = `${(translated * 100).toFixed(2)}%`;
  const color = getTranslationProgressColor(translated);
  return { language, translated, percentageString, legacyTerms, color };
}


function toText(json) {
  const { language, color, percentageString } = json;
  const padding = 30;
  const customPaddings = {
    ja: padding - 3,
    ko: padding - 3,
    'zh-cn': padding - 2,
    'zh-tw': padding - 2,
    'zh-hk': padding - 2,
  };
  const name = `${languageNames[language]} (${language})`;
  const paddedName = name.padEnd(customPaddings[language] || padding);
  return `${paddedName} ${percentageString[color]}`;
}

getAndPrintOutput();
