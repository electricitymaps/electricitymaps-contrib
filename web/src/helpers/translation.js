/* eslint-disable */
// TODO: remove once refactored

const exports = module.exports = {};

// Import locales required
const locales = {
  'en': require('../../locales/en.json'),
  [locale]: require(`../../locales/${locale}.json`),
};
const { vsprintf } = require('sprintf-js');

function translateWithLocale(locale, keyStr) {
  const keys = keyStr.split('.');
  let result = locales[locale];
  for (let i = 0; i < keys.length; i += 1) {
    if (result == null) { break; }
    result = result[keys[i]];
  }
  if (locale !== 'en' && !result) {
    return translateWithLocale('en', keyStr);
  }
  const formatArgs = Array.prototype.slice.call(arguments).slice(2); // remove 2 first
  return result && vsprintf(result, formatArgs);
}

exports.translate = function translate() {
  // Will use the `locale` global variable
  const args = Array.prototype.slice.call(arguments);
  // Prepend locale
  args.unshift(locale);
  return translateWithLocale.apply(null, args);
};

// exports.translate = function(arg) { return __(`abc${arg}`) };

exports.getFullZoneName = function getFullZoneName(zoneCode) {
  const zoneName = exports.translate(`zoneShortName.${zoneCode}.zoneName`);
  if (!zoneName) {
    return zoneCode;
  }
  const countryName = exports.translate(`zoneShortName.${zoneCode}.countryName`);
  if (!countryName) {
    return zoneName;
  }
  return `${zoneName} (${countryName})`;
};

exports.__ = exports.translate;
