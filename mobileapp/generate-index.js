var ejs = require('ejs');
var fs = require('fs');
var i18n = require('i18n');
const { vsprintf } = require('sprintf-js');

const {
  localeToFacebookLocale,
  supportedFacebookLocales,
  languageNames,
} = require('./locales-config.json');

const locales = Object.keys(languageNames);

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
    return translateWithLocale('en', keyStr);
  }
  const formatArgs = Array.prototype.slice.call(arguments).slice(2); // remove 2 first
  return result && vsprintf(result, formatArgs);
}

// duplicated from server.js
// * Long-term caching
function getHash(key, ext, obj) {
  let filename;
  if (typeof obj.assetsByChunkName[key] == 'string') {
    filename = obj.assetsByChunkName[key];
  } else {
    // assume list
    filename = obj.assetsByChunkName[key]
      .filter((d) => d.match(new RegExp('\.' + ext + '$')))[0]
  }
  return filename.replace('.' + ext, '').replace(key + '.', '');
}
const srcHashes = Object.fromEntries(locales.map((k) => {
  const obj = JSON.parse(fs.readFileSync(`${STATIC_PATH}/dist/${k}/manifest.json`));
  const BUNDLE_HASH = getHash('bundle', 'js', obj);
  const STYLES_HASH = getHash('styles', 'css', obj);
  const VENDOR_HASH = getHash('vendor', 'js', obj);
  const VENDOR_STYLES_HASH = getHash('vendor', 'css', obj);
  return [k, {
    BUNDLE_HASH, STYLES_HASH, VENDOR_HASH, VENDOR_STYLES_HASH,
  }];
}));

// * i18n
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
        bundleHash: srcHashes[locale].BUNDLE_HASH,
        vendorHash: srcHashes[locale].VENDOR_HASH,
        stylesHash: srcHashes[locale].STYLES_HASH,
        vendorStylesHash: srcHashes[locale].VENDOR_STYLES_HASH,
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
