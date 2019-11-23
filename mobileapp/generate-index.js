var ejs = require('ejs');
var fs = require('fs');
var i18n = require('i18n');

const {
  localeToFacebookLocale,
  supportedFacebookLocales,
  languageNames,
} = require('./locales-config.json');

/*
Note: Translation function should be removed and
let the client deal with all translations / formatting of ejs
*/
const localeConfigs = {};
locales.forEach((d) => {
  localeConfigs[d] = require(`${__dirname}/locales/${d}.json`);
});
function translateWithLocale(locale, keyStr) {
  const keys = keyStr.split('.');
  let result = localeConfigs[locale];
  for (let i = 0; i < keys.length; i += 1) {
    if (result == null) { break; }
    result = result[keys[i]];
  }
  if (locale !== 'en' && !result) {
    return exports.translateWithLocale('en', keyStr);
  }
  const formatArgs = Array.prototype.slice.call(arguments).slice(2); // remove 2 first
  return result && vsprintf(result, formatArgs);
}

// duplicated from server.js
function getHash(key, ext) {
    var filename;
    if (typeof obj.assetsByChunkName[key] == 'string') {
        filename = obj.assetsByChunkName[key];
    } else {
        // assume list
        filename = obj.assetsByChunkName[key]
            .filter((d) => d.match(new RegExp('\.' + ext + '$')))[0]
    }
    return filename.replace('.' + ext, '').replace(key + '.', '');
}
var obj = JSON.parse(fs.readFileSync('www/electricitymap/dist/manifest.json'));
var BUNDLE_HASH = getHash('bundle', 'js');
var STYLES_HASH = getHash('styles', 'css');
var VENDOR_HASH = getHash('vendor', 'js');
var VENDOR_STYLES_HASH = getHash('vendor', 'css');

// * i18n
const locales = Object.keys(languageNames);
i18n.configure({
    // where to store json files - defaults to './locales' relative to modules directory
    locales: locales,
    directory: __dirname + '/locales',
    defaultLocale: 'en',
    queryParameter: 'lang',
    objectNotation: true,
    updateFiles: false // whether to write new locale information to disk - defaults to true
});

locales.forEach(function(locale) {
    i18n.setLocale(locale);
    var template = ejs.compile(fs.readFileSync('../web/views/pages/index.ejs', 'utf8'));
    var html = template({
        alternateUrls: [],
        bundleHash: BUNDLE_HASH,
        vendorHash: VENDOR_HASH,
        stylesHash: STYLES_HASH,
        vendorStylesHash: VENDOR_STYLES_HASH,
        isCordova: true,
        locale: locale,
        FBLocale: localeToFacebookLocale[locale],
        supportedLocales: locales,
        supportedFBLocales: supportedFacebookLocales,
        '__': function() {
            var argsArray = Array.prototype.slice.call(arguments);
            // Prepend the first argument which is the locale
            argsArray.unshift(locale);
            return translateWithLocale.apply(null, argsArray);
        }
    });

    fs.writeFileSync('www/electricitymap/index_' + locale + '.html', html);
});
