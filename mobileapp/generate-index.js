var ejs = require('ejs');
var fs = require('fs');
var i18n = require('i18n');

var BUNDLE_HASH = JSON.parse(fs.readFileSync('www/electricitymap/dist/manifest.json')).hash;

// TODO:
// Currently, those variables are duplicated from server.js
// We should instead have a central configuration file in the `config` folder
var locales = ['da', 'de', 'en', 'es', 'fr', 'it', 'nl', 'pl', 'sv', 'zh-TW'];
var LOCALE_TO_FB_LOCALE = {
    'da': 'da_DK',
    'de': 'de_DE',
    'en': 'en_US',
    'es': 'es_ES',
    'fr': 'fr_FR',
    'it': 'it_IT',
    'nl': 'nl_NL',
    'pl': 'pl_PL',
    'sv': 'sv_SE',
    'zh-TW': 'zh_TW'
};
var SUPPORTED_FB_LOCALES = [
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
    'nl_BE',
    'nl_NL',
    'pl_PL',
    'sv_SE',
    'zh_TW'
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
      bundleHash: BUNDLE_HASH,
      isCordova: true,
      locale: locale,
      FBLocale: LOCALE_TO_FB_LOCALE[locale],
      supportedFBLocales: SUPPORTED_FB_LOCALES,
      '__': i18n.__
    });

    fs.writeFileSync('www/electricitymap/index_' + locale + '.html', html);
});
