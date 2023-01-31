const fs = require('fs');
const path = require('path');
require('colors');

const LOCALES_PATH = path.join(__dirname, '..', 'public/locales/');
const languages = fs
  .readdirSync(LOCALES_PATH)
  .filter((f) => f !== 'en.json' && f.endsWith('.json'))
  .map((f) => f.replace('.json', ''));

function getAndPrintOutput() {
  const locales = languages;
  const result = locales
    .map(translationStatusFor)
    .concat()
    .sort((a, b) => a.translated - b.translated)
    .reverse()
    .map(toText);

  console.info('\nTranslation status for all languages\n'.underline.bold);
  result.forEach((res) => console.info(res));
}

// Gets all deepest level keys from a JSON (they stand for concrete translated terms)
function getDeepKeysFromJSON(data, prefix = '') {
  if (typeof data === 'string') {
    return [prefix];
  }

  const res = Object.keys(data)
    .map((key) => getDeepKeysFromJSON(data[key], prefix ? `${prefix}___${key}` : key))
    .reduce((a, b) => a.concat(b), []);
  return res;
}

function getTermsForLanguage(language) {
  return getDeepKeysFromJSON(require(`../public/locales/${language}.json`));
}

function getTranslationProgressColor(translated) {
  if (translated > 0.9) {
    return 'green';
  }
  if (translated > 0.7) {
    return 'yellow';
  }
  if (translated > 0.5) {
    return 'magenta';
  }
  return 'red';
}

const difference = (a, b) => a.filter((c) => !b.includes(c));

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
  const padding = 10;
  const paddedName = language.padEnd(padding);
  return `${paddedName} ${percentageString[color]}`;
}

getAndPrintOutput();
