const isProduction = process.env.NODE_ENV === 'production';

// * Opbeat (must be the first thing started)
if (isProduction) {
  console.log('** Running in PRODUCTION mode **');
  var opbeat = require('opbeat').start({
    appId: 'c36849e44e',
    organizationId: '093c53b0da9d43c4976cd0737fe0f2b1',
    secretToken: process.env['OPBEAT_SECRET']
  });
}

// Modules
const compression = require('compression');
const express = require('express');
const fs = require('fs');
const http = require('http');
const i18n = require('i18n');

// Custom module
const translation = require(__dirname + '/src/helpers/translation');

const app = express();
const server = http.Server(app);

// Constants
const STATIC_PATH = process.env['STATIC_PATH'] || (__dirname + '/public');

// * Common
app.use(compression()); // Cloudflare already does gzip but we do it anyway
app.disable('etag'); // Disable etag generation (except for static)
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});

// * Templating
app.set('view engine', 'ejs');

// * i18n
const locales = ['ar', 'da', 'de', 'en', 'es', 'fr', 'it', 'ja', 'nl', 'pl', 'pt-br', 'ru', 'sv', 'zh-cn', 'zh-hk', 'zh-tw'];
i18n.configure({
  // where to store json files - defaults to './locales' relative to modules directory
  // note: detected locales are always lowercase
  locales,
  directory: __dirname + '/locales',
  defaultLocale: 'en',
  queryParameter: 'lang',
  objectNotation: true,
  updateFiles: false, // whether to write new locale information to disk
});
app.use(i18n.init);
const LOCALE_TO_FB_LOCALE = {
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
  'zh-tw': 'zh_TW',
};
// Populate using
// https://www.facebook.com/translations/FacebookLocales.xml |grep 'en_'
// and re-crawl using
// http POST https://graph.facebook.com\?id\=https://www.electricitymap.org\&amp\;scrape\=true\&amp\;locale\=\en_US,fr_FR,it_IT.......
const SUPPORTED_FB_LOCALES = [
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

// * Long-term caching
function getHash(key, ext) {
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
const obj = JSON.parse(fs.readFileSync(STATIC_PATH + '/dist/manifest.json'));
const BUNDLE_HASH = getHash('bundle', 'js');
const STYLES_HASH = getHash('styles', 'css');
const VENDOR_HASH = getHash('vendor', 'js');
const VENDOR_STYLES_HASH = getHash('vendor', 'css');

// * Opbeat
if (isProduction)
  app.use(opbeat.middleware.express())
function handleError(err) {
  if (!err) return;
  if (opbeat) opbeat.captureError(err);
  console.error(err);
}

app.get('/health', (req, res) => res.json({status: 'ok'}));
app.get('/clientVersion', (req, res) => res.send(BUNDLE_HASH));

app.get('/', (req, res) => {
  // On electricitymap.tmrow.co,
  // redirect everyone except the Facebook crawler,
  // else, we will lose all likes
  const isTmrowCo = req.get('host').indexOf('electricitymap.tmrow') !== -1;
  const isNonWWW = req.get('host') === 'electricitymap.org' ||
    req.get('host') === 'live.electricitymap.org';
  const isStaging = req.get('host') === 'staging.electricitymap.org';
  const isHTTPS = req.secure;
  const isLocalhost = req.hostname === 'localhost'; // hostname is without port

  // Redirect all non-facebook, non-staging, non-(www.* or *.tmrow.co)
  if (!isStaging && (isNonWWW || isTmrowCo) && (req.headers['user-agent'] || '').indexOf('facebookexternalhit') == -1) {
    res.redirect(301, 'https://www.electricitymap.org' + req.originalUrl);
  // Redirect all non-HTTPS and non localhost
  // Warning: this can't happen here because Cloudfare is the HTTPS proxy.
  // Node only receives HTTP traffic.
  } else if (false && !isHTTPS && !isLocalhost) {
    res.redirect(301, 'https://www.electricitymap.org' + req.originalUrl);
  } else {
    // Set locale if facebook requests it
    if (req.query.fb_locale) {
      // Locales are formatted according to
      // https://developers.facebook.com/docs/internationalization/#locales
      lr = req.query.fb_locale.split('_', 2);
      res.setLocale(lr[0]);
    }
    const { locale } = res;
    const fullUrl = 'https://www.electricitymap.org' + req.originalUrl;
    res.render('pages/index', {
      alternateUrls: locales.map(function(l) {
        if (fullUrl.indexOf('lang') != -1) {
          return fullUrl.replace('lang=' + req.query.lang, 'lang=' + l)
        } else {
          if (Object.keys(req.query).length) {
            return fullUrl + '&lang=' + l;
          } else {
            return fullUrl.replace('?', '') + '?lang=' + l;
          }
        }
      }),
      bundleHash: BUNDLE_HASH,
      vendorHash: VENDOR_HASH,
      stylesHash: STYLES_HASH,
      vendorStylesHash: VENDOR_STYLES_HASH,
      fullUrl,
      locale,
      supportedLocales: locales,
      FBLocale: LOCALE_TO_FB_LOCALE[locale],
      supportedFBLocales: SUPPORTED_FB_LOCALES,
      '__': function() {
        const argsArray = Array.prototype.slice.call(arguments);
        // Prepend the first argument which is the locale
        argsArray.unshift(locale);
        return translation.translateWithLocale.apply(null, argsArray);
      },
    });
  }
});
app.get('/v1/*', (req, res) =>
  res.redirect(301, `https://api.electricitymap.org${req.originalUrl}`));
app.get('/v2/*', (req, res) =>
  res.redirect(301, `https://api.electricitymap.org${req.originalUrl}`));
app.all('/dist/*.map', (req, res, next) => {
  if (req.headers['user-agent'] !== 'opbeat-sourcemaps-fetcher/1.0') {
    return res.status(401).json({ error: 'unauthorized' });
  }
  return next();
});

// Static routes (need to be declared at the end)
app.use(express.static(STATIC_PATH, { etag: true, maxAge: isProduction ? '24h' : '0' }));

// Start the application
server.listen(8000, () => {
  console.log('Listening on *:8000');
});
