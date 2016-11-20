var async = require('async');
var co2lib = require('./static/app/co2eq');
var d3 = require('d3');
var express = require('express');
var http = require('http');
var Memcached = require('memcached');
var moment = require('moment');
var statsd = require('node-statsd');
var MongoClient = require('mongodb').MongoClient;

var app = express();
var server = http.Server(app);

// * Common
app.use(function(req, res, next) {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});

// * Cache
var memcachedClient = new Memcached(process.env['MEMCACHED_HOST']);

// * Database
var mongoProductionCollection;
var mongoExchangeCollection;
MongoClient.connect(process.env['MONGO_URL'], function(err, db) {
    if (err) throw (err);
    console.log('Connected to database');
    mongoProductionCollection = db.collection('production');
    mongoExchangeCollection = db.collection('exchange');
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
function processDatabaseResults(countries, exchanges) {
    // Assign exchanges to countries
    d3.entries(exchanges).forEach(function(entry) {
        sortedCountryCodes = entry.key.split('->');
        entry.value.countryCodes = sortedCountryCodes;
        if (!countries[sortedCountryCodes[0]]) countries[sortedCountryCodes[0]] = {
            countryCode: sortedCountryCodes[0]
        };
        if (!countries[sortedCountryCodes[1]]) countries[sortedCountryCodes[1]] = {
            countryCode: sortedCountryCodes[1]
        };
        var country1 = countries[sortedCountryCodes[0]];
        var country2 = countries[sortedCountryCodes[1]];
        if (!country1.exchange) country1.exchange = {};
        if (!country2.exchange) country2.exchange = {};
        country1.exchange[sortedCountryCodes[1]] = entry.value.netFlow * -1.0;
        country2.exchange[sortedCountryCodes[0]] = entry.value.netFlow;
    });

    d3.keys(countries).forEach(function(k) {
        if (!countries[k])
            countries[k] = {countryCode: k};
        country = countries[k];
        // Truncate negative production values
        d3.keys(country.production).forEach(function(k) {
            if (country.production[k] !== null)
                country.production[k] = Math.max(0, country.production[k]);
        });
    });
    // Compute aggregates
    d3.values(countries).forEach(function (country) {
        country.maxProduction =
            d3.max(d3.values(country.production));
        country.totalProduction =
            d3.sum(d3.values(country.production));
        country.totalImport =
            d3.sum(d3.values(country.exchange), function(d) {
                return d >= 0 ? d : 0;
            }) || 0;
        country.totalExport =
            d3.sum(d3.values(country.exchange), function(d) {
                return d <= 0 ? -d : 0;
            }) || 0;
        country.totalNetExchange = country.totalImport - country.totalExport;
        country.maxExport =
            -Math.min(d3.min(d3.values(country.exchange)), 0) || 0;
    });

    computeCo2(countries, exchanges);

    return {countries: countries, exchanges: exchanges};
}
function computeCo2(countries, exchanges) {
    var co2calc = co2lib.Co2eqCalculator();
    co2calc.compute(countries);
    d3.entries(countries).forEach(function(o) {
        o.value.co2intensity = co2calc.assignments[o.key];
    });
    d3.values(countries).forEach(function(country) {
        country.exchangeCo2Intensities = {};
        d3.keys(country.exchange).forEach(function(k) {
            country.exchangeCo2Intensities[k] =
                country.exchange[k] > 0 ? co2calc.assignments[k] : country.co2intensity;
        });
    });
    d3.values(exchanges).forEach(function(exchange) {
        exchange.co2intensity = countries[exchange.countryCodes[exchange.netFlow > 0 ? 0 : 1]].co2intensity;
    })
}
function elementQuery(keyName, keyValue, minDate, maxDate) {
    var query = { datetime: rangeQuery(minDate, maxDate) };
    query[keyName] = keyValue
    return query;
}
function rangeQuery(minDate, maxDate) {
    var query = { $gte : minDate };
    if (maxDate) query['$lte'] = maxDate;
    return query;
}
function queryElements(keyName, keyValues, collection, minDate, maxDate, callback) {
    tasks = {};
    keyValues.forEach(function(k) {
        tasks[k] = function(callback) { 
            return collection.findOne(
                elementQuery(keyName, k, minDate, maxDate),
                { sort: [['datetime', -1]] },
                callback);
        };
    });
    return async.parallel(tasks, callback);
}
function queryLastValuesBeforeDatetime(datetime, callback) {
    var minDate = moment.utc().subtract(24, 'hours').toDate();
    var maxDate = datetime ? new Date(datetime) : undefined;
    // Get list of countries & exchanges in db
    return async.parallel([
        function(callback) {
            mongoProductionCollection.distinct('countryCode',
                {datetime: rangeQuery(minDate, maxDate)}, callback);
        },
        function(callback) {
            mongoExchangeCollection.distinct('sortedCountryCodes',
                {datetime: rangeQuery(minDate, maxDate)}, callback);
        },
    ], function(err, results) {
        if (err) return callback(err);
        countryCodes = results[0]; // production keys
        sortedCountryCodes = results[1]; // exchange keys
        // Query productions + exchanges
        async.parallel([
            function(callback) {
                return queryElements('countryCode', countryCodes,
                    mongoProductionCollection, minDate, maxDate, callback);
            },
            function(callback) {
                return queryElements('sortedCountryCodes', sortedCountryCodes,
                    mongoExchangeCollection, minDate, maxDate, callback);
            }
        ], function(err, results) {
            if (err) return callback(err);
            countries = results[0];
            exchanges = results[1];
            // This can crash, so we to try/catch
            try {
                callback(err, processDatabaseResults(countries, exchanges));
            } catch(err) {
                callback(err);
            }
        });
    });
}
function queryLastValues(callback) {
    return queryLastValuesBeforeDatetime(undefined, callback);
}

// * Static
app.use(express.static('static'));
app.use(express.static('libs'));
// * Routes
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
app.get('/v1/state', function(req, res) {
    statsdClient.increment('v1_state_GET');
    var t0 = new Date().getTime();
    function returnObj(obj, cached) {
        if (cached) statsdClient.increment('v1_state_GET_HIT_CACHE');
        var deltaMs = new Date().getTime() - t0;
        res.json({status: 'ok', data: obj, took: deltaMs + 'ms', cached: cached});
        statsdClient.timing('state_GET', deltaMs);
    }
    if (req.query.datetime) {
        queryLastValuesBeforeDatetime(req.query.datetime, function (err, result) {
            if (err) {
                statsdClient.increment('state_GET_ERROR');
                console.error(err);
                res.status(500).json({error: 'Unknown database error'});
            } else {
                returnObj(result, false);
            }
        });
    } else {
        memcachedClient.get('state', function (err, data) {
            if (err) { console.error(err); }
            if (data) returnObj(data, true);
            else {
                queryLastValues(function (err, result) {
                    if (err) {
                        statsdClient.increment('state_GET_ERROR');
                        console.error(err);
                        res.status(500).json({error: 'Unknown database error'});
                    } else {
                        memcachedClient.set('state', result, 5 * 60, function(err) {
                            if (err) console.error(err);
                        });
                        returnObj(result, false);
                    }
                });
            }
        });
    }
});
app.get('/v1/co2', function(req, res) {
    statsdClient.increment('v1_co2_GET');
    var t0 = new Date().getTime();
    var countryCode = req.query.countryCode;

    function onCo2Computed(err, countries) {
        if (err) {
            statsdClient.increment('co2_GET_ERROR');
            console.error(err);
            res.status(500).json({error: 'Unknown error'});
        } else {
            var deltaMs = new Date().getTime() - t0;
            responseObject = {
                status: 'ok',
                countryCode: countryCode,
                co2intensity: countries[countryCode].co2intensity,
                unit: 'gCo2eq/kWh',
                data: countries[countryCode]
            };
            responseObject.took = deltaMs + 'ms';
            res.json(responseObject);
            statsdClient.timing('co2_GET', deltaMs);
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
                            queryLastValues(onCo2Computed);
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
            queryLastValues(onCo2Computed);
        }
    } else {
        res.status(400).json({'error': 'Missing arguments "lon" and "lat" or "countryCode"'})
    }
});
app.get('/health', function(req, res) {
    statsdClient.increment('health_GET');
    var EXPIRATION_SECONDS = 30 * 60.0;
    mongoProductionCollection.findOne({}, {sort: [['datetime', -1]]}, function (err, doc) {
        if (err) {
            console.error(err);
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
