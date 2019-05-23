var exports = module.exports = {};

// Import all locales
var locales = {};
['ar', 'cs', 'da', 'de', 'en', 'es', 'fr', 'hr', 'it', 'ja', 'nl', 'pl', 'pt-br', 'ru', 'sk', 'sv', 'zh-cn', 'zh-hk', 'zh-tw'].forEach(function(d) {
    locales[d] = require('../../locales/' + d + '.json');
})
var vsprintf = require('sprintf-js').vsprintf;

exports.translateWithLocale = function translate(locale, keyStr) {
    var keys = keyStr.split('.');
    var result = locales[locale];
    for (var i = 0; i < keys.length; i++) {
        if (result == undefined) { break }
        result = result[keys[i]];
    }
    if (locale != 'en' && !result) {
        return exports.translateWithLocale('en', keyStr);
    } else {
        var formatArgs = Array.prototype.slice.call(arguments).slice(2); // remove 2 first
        return result && vsprintf(result, formatArgs);
    }
}
exports.translate = function() {
    // Will use the `locale` global variable
    var args = Array.prototype.slice.call(arguments);
    // Prepend locale
    args.unshift(locale)
    return exports.translateWithLocale.apply(null, args);
}

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


exports.languageNames = [
  { shortName: 'ar', name: 'اللغة العربية الفصحى' },
  { shortName: 'cs', name: 'čeština' },
  { shortName: 'da', name: 'dansk' },
  { shortName: 'de', name: 'Deutsch' },
  { shortName: 'en', name: 'English' },
  { shortName: 'es', name: 'español' },
  { shortName: 'fr', name: 'français' },
  { shortName: 'hr', name: 'hrvatski' },
  { shortName: 'it', name: 'Italiano' },
  { shortName: 'ja', name: '日本語' },
  { shortName: 'nl', name: 'Nederlands' },
  { shortName: 'pl', name: 'polski' },
  { shortName: 'pt-br', name: 'português (Brazilian)' },
  { shortName: 'ru', name: 'Русский язык' },
  { shortName: 'sk', name: 'slovenčina' },
  { shortName: 'sv', name: 'svenska' },
  { shortName: 'zh-cn', name: '中文 (Mainland China)' },
  { shortName: 'zh-hk', name: '中文 (Hong Kong)' },
  { shortName: 'zh-tw', name: '中文 (Taiwan)' },
];
