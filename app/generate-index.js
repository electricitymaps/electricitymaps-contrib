var ejs = require('ejs');
var fs = require('fs');
var i18n = require('i18n');

var BUNDLE_HASH = JSON.parse(fs.readFileSync('www/dist/manifest.json')).hash;

// * i18n
i18n.configure({
    // where to store json files - defaults to './locales' relative to modules directory
    locales: ['de', 'en', 'es', 'fr', 'it', 'nl', 'sv'],
    directory: __dirname + '/locales',
    defaultLocale: 'en',
    queryParameter: 'lang',
    objectNotation: true,
    updateFiles: false // whether to write new locale information to disk - defaults to true
});
i18n.setLocale('en');

var template = ejs.compile(fs.readFileSync('../web/views/pages/index.ejs', 'utf8'));
var html = template({
  bundleHash: BUNDLE_HASH,
  locale: 'en',
  FBLocale: 'en_US',
  supportedFBLocales: ['en_US'],
  '__': i18n.__
});

fs.writeFile('www/index.html', html, function(err) {
  if(err) {
    throw err;
  } else {
    process.exit();
  }
})
