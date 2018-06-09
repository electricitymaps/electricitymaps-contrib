var exports = module.exports = {};

// Import all locales
var locales = {};
['ar', 'da', 'de', 'en', 'es', 'fr', 'it', 'ja', 'nl', 'pl', 'pt-br', 'ru', 'sv', 'zh-cn', 'zh-hk', 'zh-tw'].forEach(function(d) {
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
