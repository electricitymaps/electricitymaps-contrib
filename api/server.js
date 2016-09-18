var express = require('express');
var http = require('http');
var app = express();
var server = http.Server(app);
var async = require('async');
var Memcached = require('memcached');
var d3 = require('d3');
var statsd = require('node-statsd');
var MongoClient = require('mongodb').MongoClient;
var co2calc = require('./static/app/co2eq').Co2eqCalculator();

// * Common
app.use(function(req, res, next) {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});

// * Cache
var memcachedClient = new Memcached(process.env['MEMCACHED_HOST']);
memcachedClient.del('production', function (err) { if (err) console.error(err); });

// * Database
var mongoCollection;
MongoClient.connect(process.env['MONGO_URL'], function(err, db) {
    if (err) throw (err);
    console.log('Connected to database');
    mongoCollection = db.collection('realtime');
    // Create indexes
    mongoCollection.createIndexes(
        [
            { datetime: -1 },
            { countryCode: 1 },
            { datetime: -1, countryCode: 1 }
        ],
        null,
        function (err, indexName) {
            if (err) console.error(err);
            else console.log('Database indexes created');
        }
    );
    server.listen(8000, function() {
        console.log('Listening on *:8000');
    });
});

// * Metrics
var statsdClient = new statsd.StatsD();
statsdClient.post = 8125;
statsdClient.host = process.env['STATSD_HOST'];
statsdClient.prefix = 'electricymap_api.';
statsdClient.socket.on('error', function(error) {
    return console.error('Error in StatsD socket: ', error);
});

// * Database methods
function queryCountry(countryCode, callback) {
    return mongoCollection.findOne(
        { countryCode: countryCode }, 
        { sort: [['datetime', -1]] },
        callback);
}
function queryAllCountries(callback) {
    countryCodes = [
        'AT',
        'BE',
        'BG',
        'BA',
        'BY',
        'CH',
        'CZ',
        'DE',
        'DK',
        'ES',
        'EE',
        'FI',
        'FR',
        'GB',
        'GR',
        'HR',
        'HU',
        'IE',
        'IS',
        'IT',
        'LT',
        'LU',
        'LV',
        'MD',
        'NL',
        'NO',
        'PL',
        'PT',
        'RO',
        'RU',
        'RS',
        'SK',
        'SI',
        'SE',
        'UA'
    ];
    return async.parallel(countryCodes.map(function (k) {
        return function(callback) { return queryCountry(k, callback); };
    }), callback);
}
function queryLastValues(callback) {
    return queryAllCountries(function (err, result) {
        // Ignore errors: just filter results
        countries = {};
        result.forEach(function(d) {
            if (d) { countries[d.countryCode] = d; }
        });
        return callback(err, countries);
    });
}
function queryAndCalculateCo2(countryCode, callback) {
    queryLastValues(function (err, countries) {
        if (err) {
            callback(err, countries);
        } else {
            // TODO: Remove the extra `data` key
            d3.keys(countries).forEach(function(k) {
                countries[k] = { data: countries[k] };
            });
            // Average out import-exports between commuting pairs
            d3.keys(countries).forEach(function(country1, i) {
                d3.keys(countries).forEach(function(country2, j) {
                    if (i < j) return;
                    var o = country1.countryCode;
                    var d = country2.countryCode;
                    var netFlows = [
                        countries[d] ? countries[d].data.exchange[o] : undefined,
                        countries[o] ? -countries[o].data.exchange[d] : undefined
                    ];
                    var netFlow = d3.mean(netFlows);
                    if (netFlow == undefined)
                        return;
                    countries[o].data.exchange[d] = -netFlow;
                    countries[d].data.exchange[o] = netFlow;
                });
            });
            // Compute aggregates
            d3.entries(countries).forEach(function (entry) {
                country = entry.value;
                // Add extra data
                country.data.maxCapacity = 
                    d3.max(d3.values(country.data.capacity));
                country.data.maxProduction = 
                    d3.max(d3.values(country.data.production));
                country.data.totalProduction = 
                    d3.sum(d3.values(country.data.production));
                country.data.totalNetExchange = 
                    d3.sum(d3.values(country.data.exchange));
                country.data.maxExport = 
                    -Math.min(d3.min(d3.values(country.data.exchange)), 0) || 0;
            });
            co2calc.compute(countries);
            if (!countries[countryCode])
                callback(Error('Country ' + countryCode + ' has no data.'), null)
            else {
                countries[countryCode].data.exchangeCo2Intensities = {}
                d3.keys(countries[countryCode].data.exchange).forEach(function(k) {
                    countries[countryCode].data.exchangeCo2Intensities[k] = co2calc.assignments[k];
                });
                callback(err, {
                    status: 'ok',
                    countryCode: countryCode,
                    co2intensity: co2calc.assignments[countryCode],
                    unit: 'gCo2eq/kWh',
                    countryData: countries[countryCode].data
                });
            }
        }
    });
}

// * Routes
app.use(express.static('static'));
app.use(express.static('vendor'));
// Backwards compat
app.get('/production', function(req, res) {
    statsdClient.increment('production_GET');
    res.redirect(301, '/v1/production');
});
app.get('/solar', function(req, res) {
    statsdClient.increment('solar_GET');
    res.redirect(301, '/v1/solar');
});
app.get('/wind', function(req, res) {
    statsdClient.increment('wind_GET');
    res.redirect(301, '/v1/wind');
});
app.get('/data/europe.topo.json', function(req, res) {
    res.redirect(301, 'http://electricitymap.tmrow.co/data/europe.topo.json');
});
// End backwards compat
app.get('/v1/wind', function(req, res) {
    statsdClient.increment('v1_wind_GET');
    res.header('Content-Encoding', 'gzip');
    res.sendFile(__dirname + '/data/wind.json.gz');
});
app.get('/v1/solar', function(req, res) {
    statsdClient.increment('v1_solar_GET');
    res.header('Content-Encoding', 'gzip');
    res.sendFile(__dirname + '/data/solar.json.gz');
});
app.get('/v1/production', function(req, res) {
    statsdClient.increment('v1_production_GET');
    var t0 = new Date().getTime();
    function returnObj(obj, cached) {
        if (cached) statsdClient.increment('v1_production_GET_HIT_CACHE');
        var deltaMs = new Date().getTime() - t0;
        res.json({status: 'ok', data: obj, took: deltaMs + 'ms', cached: cached});
        statsdClient.timing('production_GET', deltaMs);
    }
    memcachedClient.get('production', function (err, data) {
        if (data) returnObj(data, true);
        else {
            if (false && value) { returnObj(obj, true) } else {
                queryLastValues(function (err, result) {
                    if (err) {
                        statsdClient.increment('production_GET_ERROR');
                        console.error(err);
                        res.status(500).json({error: 'Unknown database error'});
                    } else {
                        memcachedClient.set('production', result, 5 * 60, function(err) {
                            if (err) console.error(err);
                        });
                        returnObj(result, false);
                    }
                });
            };
        }
    });
});
app.get('/v1/co2', function(req, res) {
    statsdClient.increment('v1_co2_GET');
    var t0 = new Date().getTime();

    function onCo2Computed(err, result) {
        if (err) {
            statsdClient.increment('co2_GET_ERROR');
            console.error(err);
            res.status(500).json({error: 'Unknown error'});
        } else {
            var deltaMs = new Date().getTime() - t0;
            result.took = deltaMs + 'ms';
            res.json(result);
            statsdClient.timing('co2_GET', deltaMs);
        }
    }

    if ((req.query.lon && req.query.lat) || req.query.countryCode) {
        if (!req.query.countryCode) {
            // Geocode
            http.get(
                'http://maps.googleapis.com/maps/api/geocode/json?latlng=' + req.query.lat + ',' + req.query.lon,
                function (geocoderResponse) {
                    var body = '';
                    geocoderResponse.on('data', function(chunk) { body += chunk; });
                    geocoderResponse.on('end', function() {
                        var obj = JSON.parse(body).results[0].address_components
                            .filter(function(d) { return d.types.indexOf('country') != -1; });
                        if (obj.length)
                            queryAndCalculateCo2(obj[0].short_name, onCo2Computed);
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
            queryAndCalculateCo2(req.query.countryCode, onCo2Computed);
        }
    } else {
        res.status(400).json({'error': 'Missing arguments "lon" and "lat" or "countryCode"'})
    }
});
app.get('/health', function(req, res) {
    statsdClient.increment('health_GET');
    var EXPIRATION_SECONDS = 30 * 60.0;
    mongoCollection.findOne({}, {sort: [['datetime', -1]]}, function (err, doc) {
        if (err) {
            console.error(err);
            res.status(500).json({error: 'Unknown database error'});
        } else {
            if (new Date().getTime() - new Date(doc.datetime).getTime() > EXPIRATION_SECONDS * 1000.0)
                res.status(500).json({error: 'Database is empty or last measurement is too old'});
            else
                res.json({status: 'ok'});
        }
    });
});
