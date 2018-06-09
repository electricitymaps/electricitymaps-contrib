var ejs = require('ejs');
var fs = require('fs');
var i18n = require('i18n');

// Custom module
var translation = require(__dirname + '/src/helpers/translation');

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

// TODO:
// Currently, those variables are duplicated from server.js
// We should instead have a central configuration file in the `config` folder
var locales = ['ar', 'da', 'de', 'en', 'es', 'fr', 'it', 'ja', 'nl', 'pl', 'pt-br', 'ru', 'sv', 'zh-cn', 'zh-hk', 'zh-tw'];
var LOCALE_TO_FB_LOCALE = {
    'ar': 'ar_AR',
    'da': 'da_DK',
    'de': 'de_DE',
    'en': 'en_US',
    'es': 'es_ES',
    'fr': 'fr_FR',
    'it': 'it_IT',
    'ja': 'ja_JP',
    'nl': 'nl_NL',
    'pt-br': 'pt_BR',
    'pl': 'pl_PL',
    'ru': 'ru_RU',
    'sv': 'sv_SE',
    'zh-cn': 'zh_CN',
    'zh-hk': 'zh_HK',
    'zh-tw': 'zh_TW'
};
var SUPPORTED_FB_LOCALES = [
    'ar_AR',
    'da_DK',
    'de_DE',
    'es_ES',
    'es_LA',
    'es_MX',
    'en_GB',
    'en_PI',
    'en_UD',
    'en_US',
    'fr_CA',
    'fr_FR',
    'it_IT',
    'ja_JP',
    'nl_BE',
    'nl_NL',
    'pl_PL',
    'pt_BR',
    'ru_RU',
    'sv_SE',
    'zh_CN',
    'zh_HK',
    'zh_TW',
];

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
        bundleHash: BUNDLE_HASH,
        vendorHash: VENDOR_HASH,
        stylesHash: STYLES_HASH,
        vendorStylesHash: VENDOR_STYLES_HASH,
        isCordova: true,
        locale: locale,
        FBLocale: LOCALE_TO_FB_LOCALE[locale],
        supportedLocales: locales,
        supportedFBLocales: SUPPORTED_FB_LOCALES,
        '__': function() {
            var argsArray = Array.prototype.slice.call(arguments);
            // Prepend the first argument which is the locale
            argsArray.unshift(locale);
            return translation.translateWithLocale.apply(null, argsArray);
        }
    });

    fs.writeFileSync('www/electricitymap/index_' + locale + '.html', html);
});
