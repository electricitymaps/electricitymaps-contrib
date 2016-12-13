var isProduction = process.env.ENV === 'production';

// * Opbeat (must be the first thing started)
if (isProduction) {
    console.log('** Running in PRODUCTION mode **');
    var opbeat = require('opbeat').start({
        appId: 'c36849e44e',
        organizationId: '093c53b0da9d43c4976cd0737fe0f2b1',
        secretToken: process.env['OPBEAT_SECRET']
    })
}

var async = require('async');
var co2lib = require('./static/app/co2eq');
var d3 = require('d3');
var express = require('express');
var http = require('http');
var Memcached = require('memcached');
var moment = require('moment');
var MongoClient = require('mongodb').MongoClient;
var statsd = require('node-statsd');
var snappy = require('snappy');

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

// * Opbeat
if (opbeat)
    app.use(opbeat.middleware.express())
function handleError(err) {
    if (opbeat) opbeat.captureError(err);
    console.error(err);
}

// * Database
var mongoProductionCollection;
var mongoExchangeCollection;
MongoClient.connect(process.env['MONGO_URL'], function(err, db) {
    if (err) throw (err);
    console.log('Connected to database');
    mongoGfsCollection = db.collection('gfs');
    mongoExchangeCollection = db.collection('exchange');
    mongoProductionCollection = db.collection('production');

    // Start the application
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
    handleError(error);
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
    });
}
function elementQuery(keyName, keyValue, minDate, maxDate) {
    var query = { datetime: rangeQuery(minDate, maxDate) };
    query[keyName] = keyValue
    return query;
}
function rangeQuery(minDate, maxDate) {
    var query = { };
    if (minDate) query['$gte'] = minDate;
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
function queryLastGfsAfter(key, datetime, callback) {
    return mongoGfsCollection.findOne(
        {'key': key, 'targetTime': rangeQuery(datetime, null)},
        { sort: [['refTime', 1]] },
        callback);
}
function queryLastGfsBefore(key, datetime, callback) {
    return mongoGfsCollection.findOne(
        {'key': key, 'targetTime': rangeQuery(null, datetime)},
        { sort: [['refTime', -1]] },
        callback);
}
function decompressGfs(callback) {
    return function (err, obj) {
        if (err) return callback(err);
        if (!obj) return callback(Error('No data found in database'));
        return snappy.uncompress(obj['data'].buffer, { asBuffer: false }, function (err, obj) {
            if (err) return callback(err);
            return callback(err, JSON.parse(obj));
        });
    }
}
function fetchForecasts(key, datetime, callback) {
    var fetchBefore = function(callback) {
        return queryLastGfsBefore(key, now, decompressGfs(callback));
    };
    var fetchAfter  = function(callback) {
        return  queryLastGfsAfter(key, now, decompressGfs(callback));
    };
    return async.parallel([fetchBefore, fetchAfter], function(err, objs) {
        if (err) return callback(err);
        return callback(null, {'forecasts': objs});
    });
}

// * Static
app.use(express.static('static'));
app.use(express.static('libs'));
// * Routes
app.get('/v1/wind', function(req, res) {
    statsdClient.increment('v1_wind_GET');
    now = moment.utc().toDate();
    // Fetch two forecasts
    fetchForecasts('wind', now, function(err, obj) {
        if (err) {
            handleError(err);
            res.status(500).send('Unknown server error');
        } else {
            res.json(obj);
        }
    });
    // memcachedClient.get('wind', function (err, data) {
    //     if (err) {
    //         handleError(err);
    //         res.status(500).send('Internal server error');
    //     } else if (data) {
    //         res.json(data);
    //     } else {
    //         res.status(404).send('Wind not found');
    //     }
    // });
    //res.header('Content-Encoding', 'gzip');
    //res.sendFile(__dirname + '/data/wind.json.gz');
});
app.get('/v1/solar', function(req, res) {
    statsdClient.increment('v1_solar_GET');
    now = moment.utc().toDate();
    // Fetch two forecasts
    fetchForecasts('solar', now, function(err, obj) {
        if (err) {
            handleError(err);
            res.status(500).send('Unknown server error');
        } else {
            res.json(obj);
        }
    });
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
                handleError(err);
                res.status(500).json({error: 'Unknown database error'});
            } else {
                returnObj(result, false);
            }
        });
    } else {
        memcachedClient.get('state', function (err, data) {
            if (err) { 
                if (opbeat) 
                    opbeat.captureError(err); 
                console.error(err); }
            if (data) returnObj(data, true);
            else {
                queryLastValues(function (err, result) {
                    if (err) {
                        statsdClient.increment('state_GET_ERROR');
                        handleError(err);
                        res.status(500).json({error: 'Unknown database error'});
                    } else {
                        memcachedClient.set('state', result, 5 * 60, function(err) {
                            if (err) {
                                handleError(err);
                            }
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

    // TODO: Rewrite this api with two promises [geocoder, state]
    function onCo2Computed(err, obj) {
        var countries = obj.countries;
        if (err) {
            statsdClient.increment('co2_GET_ERROR');
            handleError(err);
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
        elementQuery('countryCode', countryCode, minDate, maxDate),
        { sort: [['datetime', -1]] },
        function(err, doc) {
            if (err) { 
                console.log(err);
                res.status(500).json({error: 'Unknown database error'});
            } else {
                res.json(doc);
            }
        })
});
app.get('/health', function(req, res) {
    statsdClient.increment('health_GET');
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
