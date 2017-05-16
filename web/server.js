var isProduction = process.env.ENV === 'production';

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
var async = require('async');
var compression = require('compression');
var d3 = require('d3');
var express = require('express');
var fs = require('fs');
var http = require('http');
var i18n = require('i18n');

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
var locales = ['da', 'de', 'en', 'es', 'fr', 'it', 'nl', 'pl', 'sv', 'zh-cn', 'zh-hk', 'zh-tw'];
i18n.configure({
    // where to store json files - defaults to './locales' relative to modules directory
    // note: detected locales are always lowercase
    locales: locales,
    directory: __dirname + '/locales',
    defaultLocale: 'en',
    queryParameter: 'lang',
    objectNotation: true,
    updateFiles: false // whether to write new locale information to disk - defaults to true
});
app.use(i18n.init);
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
    'zh-cn': 'zh_CN',
    'zh-hk': 'zh_HK',
    'zh-tw': 'zh_TW'
};
// Populate using
// https://www.facebook.com/translations/FacebookLocales.xml |grep 'en_'
// and re-crawl using
// http POST https://graph.facebook.com\?id\=https://www.electricitymap.org\&amp\;scrape\=true\&amp\;locale\=\en_US,fr_FR,it_IT.......
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
    'zh_CN',
    'zh_HK',
    'zh_TW'
];

// * Long-term caching
var BUNDLE_HASH = !isProduction ? 'dev' :
    JSON.parse(fs.readFileSync(STATIC_PATH + '/dist/manifest.json')).hash;

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
    var isSubDomain = req.get('host').indexOf('electricitymap.tmrow.co') != -1;
    var isNonWWW = req.get('host') === 'electricitymap.org';
    var isStaging = req.get('host') === 'staging.electricitymap.org';
    if (!isStaging && (isNonWWW || isSubDomain) && (req.headers['user-agent'] || '').indexOf('facebookexternalhit') == -1) {
        // Redirect all non-facebook or non-staging
        res.redirect(301, 'https://www.electricitymap.org' + req.path);
    } else {
        // Set locale if facebook requests it
        if (req.query.fb_locale) {
            // Locales are formatted according to
            // https://developers.facebook.com/docs/internationalization/#locales
            lr = req.query.fb_locale.split('_', 2);
            res.setLocale(lr[0]);
        }
        var locale = res.locale;
        res.render('pages/index', {
            bundleHash: BUNDLE_HASH,
            locale: locale,
            supportedLocales: locales,
            FBLocale: LOCALE_TO_FB_LOCALE[locale],
            supportedFBLocales: SUPPORTED_FB_LOCALES
        });
    }
});
app.get('/v1/*', function(req, res) {
  return res.redirect(301, 'https://api.electricitymap.org' + req.path);
});
app.get('/v2/*', function(req, res) {
  return res.redirect(301, 'https://api.electricitymap.org' + req.path);
});

// Start the application
server.listen(8000, function() {
    console.log('Listening on *:8000');
});
