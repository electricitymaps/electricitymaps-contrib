const isProduction = process.env.NODE_ENV === 'production';

// Modules
const compression = require('compression');
const express = require('express');
const fs = require('fs');
const http = require('http');
const i18n = require('i18n');
const auth = require('basic-auth');
const { vsprintf } = require('sprintf-js');
const { version } = require('./package.json');

// Custom module
const {
  getSingleTranslationStatusJSON,
  getTranslationStatusJSON,
  getTranslationStatusSVG,
} = require(`${__dirname}/translation-status`);
const {
  localeToFacebookLocale,
  supportedFacebookLocales,
  languageNames,
} = require('./locales-config.json');

const app = express();
const server = http.Server(app);

// Constants
const STATIC_PATH = process.env.STATIC_PATH || (`${__dirname}/public`);

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
const locales = Object.keys(languageNames);
i18n.configure({
  // where to store json files - defaults to './locales' relative to modules directory
  // note: detected locales are always lowercase
  locales,
  directory: `${__dirname}/locales`,
  defaultLocale: 'en',
  queryParameter: 'lang',
  objectNotation: true,
  updateFiles: false, // whether to write new locale information to disk
});

app.use(i18n.init);
// For supportedFacebookLocales:
// Populate using
// https://developers.facebook.com/docs/messenger-platform/messenger-profile/supported-locales/
// and re-crawl using
// http POST https://graph.facebook.com\?id\=https://www.electricitymap.org\&amp\;scrape\=true\&amp\;locale\=\en_US,fr_FR,it_IT.......

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

// * Long-term caching
function getHash(key, ext, obj) {
  let filename;
  if (typeof obj.assetsByChunkName[key] === 'string') {
    filename = obj.assetsByChunkName[key];
  } else {
    // assume list
    filename = obj.assetsByChunkName[key]
      .filter(d => d.match(new RegExp(`\.${ext}$`)))[0];
  }
  return filename.replace(`.${ext}`, '').replace(`${key}.`, '');
}

const manifest = JSON.parse(fs.readFileSync(`${STATIC_PATH}/dist/manifest.json`));

app.get('/health', (req, res) => res.json({ status: 'ok' }));
app.get('/clientVersion', (req, res) => res.send(version));

// Translation status
app.get('/translationstatus/badges.svg', (req, res) => {
  res.set('Content-Type', 'image/svg+xml;charset=utf-8');
  res.end(getTranslationStatusSVG(locales));
});
app.get('/translationstatus', (req, res) => res.json(getTranslationStatusJSON(locales)));
app.get('/translationstatus/:language', (req, res) => res.json(getSingleTranslationStatusJSON(req.params.language)));

// API
app.get('/v1/*', (req, res) => res.redirect(301, `https://api.electricitymap.org${req.originalUrl}`));
app.get('/v2/*', (req, res) => res.redirect(301, `https://api.electricitymap.org${req.originalUrl}`));

// Source maps
app.all('/dist/*.map', (req, res, next) => {
  // Allow sentry
  if ([
    '35.184.238.160',
    '104.155.159.182',
    '104.155.149.19',
    '130.211.230.102',
  ].indexOf(req.headers['x-forwarded-for']) !== -1) {
    return res.status(401).json({ error: 'unauthorized' });
  }
  return next();
});

// Static files
app.use(express.static(STATIC_PATH, { etag: true, maxAge: isProduction ? '24h' : '0' }));

// App routes (managed by React Router)
app.use('/', (req, res) => {
  // On electricitymap.tmrow.co,
  // redirect everyone except the Facebook crawler,
  // else, we will lose all likes
  const isTmrowCo = req.get('host').indexOf('electricitymap.tmrow') !== -1;
  const isNonWWW = req.get('host') === 'electricitymap.org'
    || req.get('host') === 'live.electricitymap.org';
  const isStaging = req.get('host').includes('staging');
  const isHTTPS = req.secure;
  const isLocalhost = req.hostname === 'localhost'; // hostname is without port

  // Redirect all non-facebook, non-staging, non-(www.* or *.tmrow.co)
  if (!isStaging && (isNonWWW || isTmrowCo) && (req.headers['user-agent'] || '').indexOf('facebookexternalhit') == -1) {
    res.redirect(301, `https://www.electricitymap.org${req.originalUrl}`);
  // Redirect all non-HTTPS and non localhost
  // Warning: this can't happen here because Cloudfare is the HTTPS proxy.
  // Node only receives HTTP traffic.
  } else if (false && !isHTTPS && !isLocalhost) {
    res.redirect(301, `https://www.electricitymap.org${req.originalUrl}`);
  } else {
    // Set locale if facebook requests it
    if (req.query.fb_locale) {
      // Locales are formatted according to
      // https://developers.facebook.com/docs/internationalization/#locales
      lr = req.query.fb_locale.split('_', 2);
      res.setLocale(lr[0]);
    }
    const { locale } = res;
    const fullUrl = `https://www.electricitymap.org${req.originalUrl}`;

    // basic auth for premium access
    if (process.env.BASIC_AUTH_CREDENTIALS) {
      const user = auth(req);
      let authorized = false;
      if (user) {
        process.env.BASIC_AUTH_CREDENTIALS.split(',').forEach((cred) => {
          const [name, pass] = cred.split(':');
          if (name === user.name && pass === user.pass) {
            authorized = true;
          }
        });
      }
      if (!authorized) {
        res.statusCode = 401;
        res.setHeader('WWW-Authenticate', 'Basic realm="Premium access to electricitymap.org"');
        res.end('Access denied');
        return;
      }
      res.cookie('electricitymap-token', process.env.ELECTRICITYMAP_TOKEN);
    }
    res.render('pages/index', {
      alternateUrls: locales.map((l) => {
        if (fullUrl.indexOf('lang') !== -1) {
          return fullUrl.replace(`lang=${req.query.lang}`, `lang=${l}`);
        }
        if (Object.keys(req.query).length) {
          return `${fullUrl}&lang=${l}`;
        }
        return `${fullUrl.replace('?', '')}?lang=${l}`;
      }),
      bundleHash: getHash('bundle', 'js', manifest),
      vendorHash: getHash('vendor', 'js', manifest),
      stylesHash: getHash('styles', 'css', manifest),
      vendorStylesHash: getHash('vendor', 'css', manifest),
      // Make the paths absolute as that's required for BrowserHistory routing
      // to work normally and it's also ok when used with the https:// protocol
      // as resources are mounted to a fixed location.
      // Note: `resolvePath` is executed on the client as well,
      // as it is used in react components. We can't therefore include any variables
      // in its closure. It would be better to pass a `pathPrefix` instead.
      resolvePath: (!isProduction || isStaging)
        ? relativePath => `/${relativePath}`
        : relativePath =>
          // Note we here point to static hosting in order to make
          // sure we can serve older bundle versions
          `https://static.electricitymap.org/public_web/${relativePath}`,
      fullUrl,
      locale,
      locales: { en: localeConfigs.en, [locale]: localeConfigs[locale] },
      supportedLocales: locales,
      FBLocale: localeToFacebookLocale[locale],
      supportedFBLocales: supportedFacebookLocales,
      __() {
        const argsArray = Array.prototype.slice.call(arguments);
        // Prepend the first argument which is the locale
        argsArray.unshift(locale);
        return translateWithLocale.apply(null, argsArray);
      },
    });
  }
});

if (isProduction) {
  app.get('/*', (req, res) =>
    // Redirect all requests except root to static
    res.redirect(`https://static.electricitymap.org/public_web${req.originalUrl}`));
}

// Start the application
server.listen(process.env.PORT, () => {
  console.log(`Listening on *:${process.env.PORT}`);
});
