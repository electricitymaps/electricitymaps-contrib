var isProduction = process.env.NODE_ENV === 'production';

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
var compression = require('compression');
var d3 = require('d3');
var express = require('express');
var fs = require('fs');
var http = require('http');
var i18n = require('i18n');
var geoip = require('geoip-lite');

// Custom module
var translation = require(__dirname + '/app/translation');

var app = express();
var server = http.Server(app);

// * Common
app.use(compression()); // Cloudflare already does gzip but we do it anyway
app.disable('etag'); // Disable etag generation (except for static)
app.use(function(req, res, next) {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});

// * Static and templating
var STATIC_PATH = process.env['STATIC_PATH'] || (__dirname + '/public');
app.use(express.static(STATIC_PATH, {etag: true, maxAge: isProduction ? '24h': '0'}));
app.set('view engine', 'ejs');

// * i18n
var locales = ['ar', 'da', 'de', 'en', 'es', 'fr', 'it', 'ja', 'nl', 'pl', 'pt-br', 'sv', 'zh-cn', 'zh-hk', 'zh-tw'];
i18n.configure({
    // where to store json files - defaults to './locales' relative to modules directory
    // note: detected locales are always lowercase
    locales: locales,
    directory: __dirname + '/locales',
    defaultLocale: 'en',
    queryParameter: 'lang',
    objectNotation: true,
    updateFiles: false, // whether to write new locale information to disk
});
app.use(i18n.init);
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
    'sv': 'sv_SE',
    'zh-cn': 'zh_CN',
    'zh-hk': 'zh_HK',
    'zh-tw': 'zh_TW'
};
// Populate using
// https://www.facebook.com/translations/FacebookLocales.xml |grep 'en_'
// and re-crawl using
// http POST https://graph.facebook.com\?id\=https://www.electricitymap.org\&amp\;scrape\=true\&amp\;locale\=\en_US,fr_FR,it_IT.......
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
    'sv_SE',
    'zh_CN',
    'zh_HK',
    'zh_TW'
];

// * Long-term caching
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
var obj = JSON.parse(fs.readFileSync(STATIC_PATH + '/dist/manifest.json'));
var BUNDLE_HASH = getHash('bundle', 'js');
var VENDOR_HASH = getHash('vendor', 'js');
var STYLES_HASH = getHash('styles', 'css');

// * Opbeat
if (isProduction)
    app.use(opbeat.middleware.express())
function handleError(err) {
    if (!err) return;
    if (opbeat) opbeat.captureError(err);
    console.error(err);
}

app.get('/health', function(req, res) {
    return res.json({status: 'ok'});
});
app.get('/clientVersion', function(req, res) {
    res.send(BUNDLE_HASH);
});
app.get('/', function(req, res) {
    // On electricitymap.tmrow.co,
    // redirect everyone except the Facebook crawler,
    // else, we will lose all likes
    var isSubDomain = req.get('host').indexOf('electricitymap.tmrow') != -1;
    var isNonWWW = req.get('host') === 'electricitymap.org';
    var isStaging = req.get('host') === 'staging.electricitymap.org';
    var isHTTPS = req.secure;
    var isLocalhost = req.hostname == 'localhost'; // hostname is without port
    var ip = req.headers['cf-connecting-ip'] || req.ip;

    // Redirect all non-facebook, non-staging, non-(www.* or *.tmrow.co)
    if (!isStaging && (isNonWWW || isSubDomain) && (req.headers['user-agent'] || '').indexOf('facebookexternalhit') == -1) {
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
        var locale = res.locale;
        var fullUrl = 'https://www.electricitymap.org' + req.originalUrl;
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
            fullUrl: fullUrl,
            locale: locale,
            supportedLocales: locales,
            FBLocale: LOCALE_TO_FB_LOCALE[locale],
            supportedFBLocales: SUPPORTED_FB_LOCALES,
            geo: geoip.lookup(ip),
            '__': function() {
                var argsArray = Array.prototype.slice.call(arguments);
                // Prepend the first argument which is the locale
                argsArray.unshift(locale);
                return translation.translateWithLocale.apply(null, argsArray);
            }
        });
    }
});
app.get('/v1/*', function(req, res) {
  return res.redirect(301, 'https://api.electricitymap.org' + req.originalUrl);
});
app.get('/v2/*', function(req, res) {
  return res.redirect(301, 'https://api.electricitymap.org' + req.originalUrl);
});

// Start the application
server.listen(8000, function() {
    console.log('Listening on *:8000');
});
