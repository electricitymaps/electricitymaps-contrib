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
var Memcached = require('memcached');
var moment = require('moment');
var MongoClient = require('mongodb').MongoClient;
var i18n = require('i18n');

//var statsd = require('node-statsd'); // TODO: Remove

// Custom modules
global.__base = __dirname;
var db = require('../shared/database')

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
i18n.configure({
    // where to store json files - defaults to './locales' relative to modules directory
    locales: ['en', 'fr', 'it', 'nl'],
    directory: __dirname + '/locales',
    defaultLocale: 'en',
    queryParameter: 'lang',
    objectNotation: true,
    updateFiles: false // whether to write new locale information to disk - defaults to true
});
app.use(i18n.init);
LOCALE_TO_FB_LOCALE = {
    'en': 'en_US',
    'fr': 'fr_FR',
    'it': 'it_IT',
    'nl': 'nl_NL'
};
// Populate using
// https://www.facebook.com/translations/FacebookLocales.xml |grep 'en_'
// and re-crawl using
// http POST https://graph.facebook.com\?id\=https://www.electricitymap.org\&amp\;scrape\=true\&amp\;locale\=\en_US,fr_FR,it_IT.......
SUPPORTED_FB_LOCALES = [
    'en_GB',
    'en_IN',
    'en_PI',
    'en_UD',
    'en_US',
    'fr_CA',
    'fr_FR',
    'it_IT',
    'nl_BE',
    'nl_NL',
];

// * Long-term caching
var BUNDLE_HASH = !isProduction ? 'dev' : 
    JSON.parse(fs.readFileSync(STATIC_PATH + '/dist/manifest.json')).hash;

// * Cache
var memcachedClient = new Memcached(process.env['MEMCACHED_HOST']);

// * Opbeat
if (isProduction)
    app.use(opbeat.middleware.express())
function handleError(err) {
    if (!err) return;
    if (opbeat) opbeat.captureError(err);
    console.error(err);
}

// * Database
var mongoProductionCollection;
var mongoExchangeCollection;
db.connect(function(err, db) {
    if (err) throw (err);
    console.log('Connected to database');
    mongoExchangeCollection = db.collection('exchange');
    mongoProductionCollection = db.collection('production');

    // Start the application
    server.listen(8000, function() {
        console.log('Listening on *:8000');
    });
});

// * Metrics
// var statsdClient = new statsd.StatsD();
// statsdClient.post = 8125;
// statsdClient.host = process.env['STATSD_HOST'];
// statsdClient.prefix = 'electricymap_api.';
// statsdClient.socket.on('error', function(error) {
//     handleError(error);
// });

// * Routes
app.get('/v1/wind', function(req, res) {
    var t0 = (new Date().getTime());
    //statsdClient.increment('v1_wind_GET');
    var cacheQuery = false;//req.query.datetime == null;
    var cacheResponse = req.query.datetime == null;
    now = req.query.datetime ? new Date(req.query.datetime) : moment.utc().toDate();
    getParsedForecasts('wind', now, cacheQuery, function(err, obj) {
        if (err) {
            handleError(err);
            res.status(500).send('Unknown server error');
        } else if (!obj) {
            res.status(500).send('No data');
        } else {
            var deltaMs = new Date().getTime() - t0;
            obj['took'] = deltaMs + 'ms';
//            statsdClient.timing('wind_GET', deltaMs);
            if (cacheResponse) {
                var beforeTargetTime = moment(obj.forecasts[0][0].header.refTime)
                    .add(obj.forecasts[0][0].header.forecastTime, 'hours');
                var afterTargetTime = moment(obj.forecasts[1][0].header.refTime)
                    .add(obj.forecasts[1][0].header.forecastTime, 'hours');
                // This cache system ignore the fact that a newer forecast,
                // for the same target, can be fetched.
                res.setHeader('Cache-Control', 'public');
                // Expires at/after the upper bound (to force refresh after)
                res.setHeader('Expires', afterTargetTime.toDate().toUTCString());
                // Last-modified at the lower bound (to force refresh before)
                res.setHeader('Last-Modified', beforeTargetTime.toDate().toUTCString());
            }
            res.json(obj);
        }
    });
});
app.get('/v1/solar', function(req, res) {
    var t0 = (new Date().getTime());
    //statsdClient.increment('v1_solar_GET');
    var cacheQuery = false;//req.query.datetime == null;
    var cacheResponse = req.query.datetime == null;
    now = req.query.datetime ? new Date(req.query.datetime) : moment.utc().toDate();
    getParsedForecasts('solar', now, cacheQuery, function(err, obj) {
        if (err) {
            handleError(err);
            res.status(500).send('Unknown server error');
        } else if (!obj) {
            res.status(500).send('No data');
        } else {
            var deltaMs = new Date().getTime() - t0;
            obj['took'] = deltaMs + 'ms';
                //statsdClient.timing('solar_GET', deltaMs);
            if (cacheResponse) {
                var beforeTargetTime = moment(obj.forecasts[0].header.refTime)
                    .add(obj.forecasts[0].header.forecastTime, 'hours');
                var afterTargetTime = moment(obj.forecasts[1].header.refTime)
                    .add(obj.forecasts[1].header.forecastTime, 'hours');
                // This cache system ignore the fact that a newer forecast,
                // for the same target, can be fetched.
                res.setHeader('Cache-Control', 'public');
                // Expires at/after the upper bound (to force refresh after)
                res.setHeader('Expires', afterTargetTime.toDate().toUTCString());
                // Last-modified at the lower bound (to force refresh before)
                res.setHeader('Last-Modified', beforeTargetTime.toDate().toUTCString());
                res.json(obj);
            }
        }
    });
});
app.get('/v1/state', function(req, res) {
    //statsdClient.increment('v1_state_GET');
    var t0 = new Date().getTime();
    function returnObj(obj, cached) {
        var deltaMs = new Date().getTime() - t0;
        res.json({status: 'ok', data: obj, took: deltaMs + 'ms', cached: cached});
    }
    if (req.query.datetime) {
        // Ignore requests in the future
        if (moment(req.query.datetime) > moment.now())
            returnObj({countries: {}, exchanges: {}}, false);
        db.queryLastValuesBeforeDatetime(req.query.datetime, function (err, result) {
            if (err) {
                //statsdClient.increment('state_GET_ERROR');
                handleError(err);
                res.status(500).json({error: 'Unknown database error'});
            } else {
                returnObj(result, false);
            }
        });
    } else {
        return db.getCached('state',
            function (err, data, cached) {
                if (err) {
                    if (opbeat) 
                        opbeat.captureError(err);
                    console.error(err);
                    return res.status(500)
                        .json({error: 'Unknown database error'});
                }
                returnObj(data || {'countries': [], 'exchanges': []}, cached);
            },
            5 * 60,
            db.queryLastValues);
    }
});
app.get('/v1/co2', function(req, res) {
    //statsdClient.increment('v1_co2_GET');
    var t0 = new Date().getTime();
    var countryCode = req.query.countryCode;

    function getCachedState(callback) {
        return db.getCached('state',
            callback,
            5 * 60,
            db.queryLastValues);
    }

    // TODO: Rewrite this api with two promises [geocoder, state]
    function onCo2Computed(err, obj, cached) {
        var countries = obj.countries;
        if (err) {
            //statsdClient.increment('co2_GET_ERROR');
            handleError(err);
            res.status(500).json({error: 'Unknown error'});
        } else {
            var deltaMs = new Date().getTime() - t0;
            responseObject = {
                status: 'ok',
                countryCode: countryCode,
                co2intensity: (countries[countryCode] || {}).co2intensity,
                unit: 'gCo2eq/kWh',
                data: countries[countryCode],
                cached: cached
            };
            responseObject.took = deltaMs + 'ms';
            res.json(responseObject);
            //statsdClient.timing('co2_GET', deltaMs);
        }
    }

    if ((req.query.lon && req.query.lat) || countryCode) {
        if (!countryCode) {
            // Geocode
            http.get(
                'http://maps.googleapis.com/maps/api/geocode/json?latlng=' + req.query.lat + ',' + req.query.lon,
                function (geocoderResponse) {
                    var body = '';
                    geocoderResponse.on('data', function(chunk) { body += chunk; });
                    geocoderResponse.on('end', function() {
                        var obj = JSON.parse(body).results[0].address_components
                            .filter(function(d) { return d.types.indexOf('country') != -1; });
                        if (obj.length) {
                            countryCode = obj[0].short_name;
                            getCachedState(onCo2Computed);
                        }
                        else {
                            console.error('Geocoder returned no usable results');
                            res.status(500).json({error: 'Error while geocoding'});
                        }
                    });
                }
            ).on('error', (e) => {
                console.error(`Error while geocoding: ${e.message}`);
                res.status(500).json({error: 'Error while geocoding'});
            });
        } else {
            getCachedState(onCo2Computed);
        }
    } else {
        res.status(400).json({'error': 'Missing arguments "lon" and "lat" or "countryCode"'})
    }
});
app.get('/v1/exchanges', function(req, res) {
    var countryCode = req.query.countryCode;
    var datetime = req.query.datetime;
    if (!countryCode) {
        res.status(400).json({'error': 'Missing argument "countryCode"'});
        return;
    }
    var maxDate = datetime ? new Date(datetime) : undefined;
    var minDate = (moment(maxDate) || moment.utc()).subtract(24, 'hours').toDate();
    mongoExchangeCollection.distinct('sortedCountryCodes',
        {datetime: db.rangeQuery(minDate, maxDate)},
        function(err, sortedCountryCodes) {
            if (err) {
                handleError(err);
                res.status(500).json({error: 'Unknown database error'});
            } else {
                sortedCountryCodes = sortedCountryCodes.filter(function(d) {
                    var arr = d.split('->')
                    var from = arr[0]; var to = arr[1];
                    return (from === countryCode || to === countryCode);
                });
                db.queryElements('sortedCountryCodes', sortedCountryCodes,
                    mongoExchangeCollection, minDate, maxDate,
                    function(err, data) {
                        if (err) {
                            handleError(err);
                            res.status(500).json({error: 'Unknown database error'});
                        } else {
                            res.json({status: 'ok', data: data});
                        }
                    });
            }
        })
});
app.get('/v1/production', function(req, res) {
    var countryCode = req.query.countryCode;
    var datetime = req.query.datetime;
    if (!countryCode) {
        res.status(400).json({'error': 'Missing argument "countryCode"'});
        return;
    }
    var maxDate = datetime ? new Date(datetime) : undefined;
    var minDate = (moment(maxDate) || moment.utc()).subtract(24, 'hours').toDate();
    mongoProductionCollection.findOne(
        db.elementQuery('countryCode', countryCode, minDate, maxDate),
        { sort: [['datetime', -1]] },
        function(err, doc) {
            if (err) { 
                handleError(err);
                res.status(500).json({error: 'Unknown database error'});
            } else {
                res.json(doc);
            }
        })
});

// *** V2 ***
function handleForecastQuery(key, req, res) {
    var t0 = (new Date().getTime());
    //statsdClient.increment('v1_wind_GET');
    var cacheResponse = req.query.datetime == null;
    if (!req.query.refTime)
        return res.status(400).json({'error': 'Parameter `refTime` is missing'});
    if (!req.query.targetTime)
        return res.status(400).json({'error': 'Parameter `targetTime` is missing'});
    db.queryGfsAt(key, req.query.refTime, req.query.targetTime, (err, obj) => {
        if (err) {
            handleError(err);
            return res.status(500).send('Unknown server error');
        } else if (!obj) {
            return res.status(404).send('Forecast was not found');
        } else {
            return db.decompressGfs(obj['data'].buffer, (err, result) => {
                if (err) {
                    handleError(err);
                    return res.status(500).send('Unknown server error');
                }
                // statsdClient.timing('wind_GET', deltaMs);
                if (cacheResponse) {
                    // Cache for max 1d
                    res.setHeader('Cache-Control', 'public, max-age=86400, s-max-age=86400');
                    // Last-modified at the lower bound (to force refresh before)
                    res.setHeader('Last-Modified',
                        (obj['updatedAt'] || obj['createdAt']).toUTCString());
                }
                var deltaMs = new Date().getTime() - t0;
                res.json({
                    data: result,
                    took: deltaMs + 'ms'
                });
            });
        }
    });
}
app.get('/v2/gfs/:key', function(req, res) {
    return handleForecastQuery(req.params.key, req, res);
});

app.get('/v2/co2LastDay', function(req, res) {
    // TODO: Remove
    res.redirect(301, '/v2/history?countryCode=' + req.query.countryCode);
});
app.get('/v2/history', function(req, res) {
    var countryCode = req.query.countryCode;
    if (!countryCode) return res.status(400).send('countryCode required');

    return db.getCached('HISTORY_' + countryCode,
        function (err, data, cached) {
            if (err) {
                if (opbeat)
                    opbeat.captureError(err); 
                console.error(err);
                res.status(500).send('Unknown database error');
            // } else if (!data) {
            //     res.status(500).send('No data was found');
            } else {
                res.json({ 'data': data, 'cached': cached })
            }
        });
});

// *** UNVERSIONED ***
app.get('/health', function(req, res) {
    //statsdClient.increment('health_GET');
    var EXPIRATION_SECONDS = 30 * 60.0;
    mongoProductionCollection.findOne({}, {sort: [['datetime', -1]]}, function (err, doc) {
        if (err) {
            console.error(err);
            handleError(err);
            res.status(500).json({error: 'Unknown database error'});
        } else {
            var deltaMs = new Date().getTime() - new Date(doc.datetime).getTime();
            if (deltaMs < 0 && deltaMs > EXPIRATION_SECONDS * 1000.0)
                res.status(500).json({error: 'Database is empty or last measurement is too old'});
            else
                res.json({status: 'ok'});
        }
    });
});
app.get('/clientVersion', function(req, res) {
    res.send(BUNDLE_HASH);
});
app.get('/', function(req, res) {
    // On electricitymap.tmrow.co,
    // redirect everyone except the Facebook crawler,
    // else, we will lose all likes
    var isSubDomain = req.get('host').indexOf('electricitymap.tmrow.co') != -1;
    if (isSubDomain && (req.headers['user-agent'] || '').indexOf('facebookexternalhit') == -1) {
        // Redirect
        res.redirect(301, 'http://www.electricitymap.org' + req.path);
    } else {
        // Set locale if facebook requests it
        if (req.query.fb_locale) {
            // Locales are formatted according to 
            // https://developers.facebook.com/docs/internationalization/#locales
            lr = req.query.fb_locale.split('_', 2);
            res.setLocale(lr[0]);
        }
        res.render('pages/index', {
            bundleHash: BUNDLE_HASH,
            locale: res.locale,
            FBLocale: LOCALE_TO_FB_LOCALE[res.locale],
            supportedFBLocales: SUPPORTED_FB_LOCALES,
            useAnalytics: req.get('host').indexOf('electricitymap') != -1
        });
    }
});
