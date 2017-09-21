var exports = module.exports = {};

// Import all locales
var locales = {};
['ar', 'da', 'de', 'en', 'es', 'fr', 'it', 'nl', 'pl', 'sv', 'zh-cn', 'zh-hk', 'zh-tw'].forEach(function(d) {
    locales[d] = require('../locales/' + d + '.json');
})
var sprintf = require('sprintf-js').sprintf;

exports.translateWithLocale = translateWithLocale = function(locale, keyStr) {
    keys = keyStr.split('.');
    result = locales[locale];
    for (var i = 0; i < keys.length; i++) {
        if (result == undefined) { break }
        result = result[keys[i]];
    }
    if (locale != 'en' && !result) {
        translateWithLocale(keyStr, 'en');
    } else {
        formatArgs = Array.prototype.slice.call(arguments).slice(2); // remove 2 first
        return sprintf(result, formatArgs);
    }
}
exports.translate = function(keyStr) {
    // Will use the `locale` global variable
    return translateWithLocale(locale, keyStr);
}
