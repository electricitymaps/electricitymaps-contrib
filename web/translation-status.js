const { reverse, flatMap, difference, size, sortBy } = require('lodash');
const { LOCALES_LIST } = require('./src/helpers/translation');

// Gets all deepest level keys from a JSON (they stand for concrete translated terms)
function getDeepKeysFromJSON(data, prefix = '') {
  if (typeof data === 'string') return [prefix];
  return flatMap(data, (d, i) => getDeepKeysFromJSON(d, `${prefix}___${i}`));
}

function getTermsForLanguage(language) {
  return getDeepKeysFromJSON(require(`${__dirname}/locales/${language}.json`));
}

function getTranslationProgressColor(translated) {
  if (translated > 0.99) return 'brightgreen';
  if (translated > 0.9) return 'green';
  if (translated > 0.7) return 'yellow';
  if (translated > 0.5) return 'orange';
  return 'red';
}

function translationStatusFor(language) {
  const totalWords = getTermsForLanguage('en'); // the default language in locale settings
  const translatedWords = getTermsForLanguage(language);
  const untranslatedWords = difference(totalWords, translatedWords);
  const legacyTerms = size(difference(translatedWords, totalWords));
  const translated = 1 - (size(untranslatedWords) / size(totalWords));
  const color = getTranslationProgressColor(translated);
  return { language, translated, legacyTerms, color };
}

function toPercent(json) {
  return {
    ...json,
    translated: `${(json.translated * 100).toFixed(2)}%`,
  };
}

function getTranslationStatusJSON(language) {
  if (language) {
    return toPercent(translationStatusFor(language));
  }
  // If the language is not specified, list statuses for all
  // locales in descending order by translation percentage.
  return reverse(sortBy(LOCALES_LIST.map(translationStatusFor), 'translated')).map(toPercent);
}

// A link to a custom generated badge (https://github.com/badges/shields) based on translation.
function getTranslationBadge({ language, translated, color }) {
  return `https://img.shields.io/badge/${language.replace('-', '--')}-${translated}25-${color}.svg`;
}

// Compile a full list of translation badges into a SVG.
function getTranslationStatusSVG() {
  return `
    <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" height="${24 * size(LOCALES_LIST)}">
      ${getTranslationStatusJSON().map((translation, index) => `<image y="${24 * index}" xlink:href="${getTranslationBadge(translation)}"/>`).join('')}
    </svg>
  `;
}

module.exports = {
  getTranslationStatusJSON,
  getTranslationStatusSVG,
};
