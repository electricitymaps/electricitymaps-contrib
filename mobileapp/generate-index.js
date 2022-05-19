var ejs = require('ejs');
var fs = require('fs');

const STATIC_PATH = 'www/electricitymap';

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
  localeConfigs[d] = require(`${__dirname}/www/electricitymap/locales/${d}.json`);
});

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

const template = ejs.compile(fs.readFileSync('../web/views/pages/index.ejs', 'utf8'));
const manifest = JSON.parse(fs.readFileSync(`${STATIC_PATH}/dist/manifest.json`));

locales.forEach(function(locale) {
    const html = template({
        maintitle: localeConfigs[locale || 'en'].misc.maintitle,
        alternateUrls: [],
        bundleHash: getHash('bundle', 'js', manifest),
        vendorHash: getHash('vendor', 'js', manifest),
        bundleStylesHash: getHash('bundle', 'css', manifest),
        vendorStylesHash: getHash('vendor', 'css', manifest),
        // Keep using relative resource paths on mobile platforms as that's
        // the way to keep them working with file:// protocol and HashHistory
        // doesn't require paths to be absolute.
        resolvePath: function(relativePath) { return relativePath; },
        isCordova: true,
        FBLocale: localeToFacebookLocale[locale],
        supportedLocales: locales,
        supportedFBLocales: supportedFacebookLocales,
    });

    fs.writeFileSync('www/electricitymap/index_' + locale + '.html', html);
});
