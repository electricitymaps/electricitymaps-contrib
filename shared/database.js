var exports = module.exports = {};

if (__base) module.paths.push(__base + '/node_modules');

// * Modules
var async = require('async');
var d3 = require('d3');
var snappy = require('snappy');
var Memcached = require('memcached');
var moment = require('moment');

// * Custom
var co2eq_parameters = require('./co2eq_parameters');
var co2lib = require('./co2eq');

// * Cache
memcachedClient = new Memcached(process.env['MEMCACHED_HOST']);

// * Database
var mongoGfsCollection;
var mongoExchangeCollection;
var mongoPriceCollection;
var mongoProductionCollection;
exports.connect = function (callback) {
    require('mongodb').MongoClient.connect(process.env['MONGO_URL'], function(err, db) {
        if (err) throw (err);
        mongoGfsCollection = db.collection('gfs');
        mongoExchangeCollection = db.collection('exchange');
        mongoPriceCollection = db.collection('price');
        mongoProductionCollection = db.collection('production');
        callback(err, db);
    });
}

// * Cache methods
exports.getCached = function (key, callback, cacheSeconds, asyncComputeFunction) {
    memcachedClient.get(key, function (err, obj) {
        if (err && asyncComputeFunction) {
            console.error(err);
        }
        if (!asyncComputeFunction || obj) {
            return callback(err, obj);
        } else {
            return asyncComputeFunction(function (err, obj) {
                if (!err) {
                    memcachedClient.set(key, obj, cacheSeconds, function (err) {
                        if (err) console.error(err);
                    });
                }
                return callback(err, obj);
            });
        }
    });
}
exports.setCache = function (key, obj, cacheSeconds, callback) {
    return memcachedClient.set(key, obj, cacheSeconds, function (err) {
        callback(err);
    });
}

// * Database methods
function processDatabaseResults(countries, exchanges, prices) {
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

    // Assign prices to countries
    d3.entries(prices).forEach(function(entry) {
        if (countries[entry.key])
            countries[entry.key].price = {
                datetime: entry.value.datetime,
                value: entry.value.price
            }
    });

    // Add countryCode
    d3.keys(countries).forEach(function(k) {
        if (!countries[k])
            countries[k] = {countryCode: k};
        country = countries[k];
    });
    // Compute aggregates
    d3.values(countries).forEach(function(country) {
        country.maxProduction =
            d3.max(d3.values(country.production));
        country.totalProduction =
            d3.sum(d3.values(country.production));
        country.maxStorage =
            d3.max(d3.values(country.storage || {}));
        country.totalStorage =
            d3.sum(d3.values(country.storage || {}));
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
        country.maxImport =
            Math.max(d3.max(d3.values(country.exchange)), 0) || 0;
    });

    computeCo2(countries, exchanges);

    return {countries: countries, exchanges: exchanges};
}
function computeCo2(countries, exchanges) {
    var assignments = co2lib.compute(countries);
    d3.entries(countries).forEach(function(o) {
        o.value.co2intensity = assignments[o.key];
    });
    d3.values(countries).forEach(function(country) {
        country.exchangeCo2Intensities = {};
        d3.keys(country.exchange).forEach(function(k) {
            // Note that for imports of countries with unknown co2intensity
            // the current country co2intensity is used (see co2eq.js)
            country.exchangeCo2Intensities[k] =
                country.exchange[k] > 0 ?
                    (assignments[k] || country.co2intensity) :
                    country.co2intensity;
        });
        country.productionCo2Intensities = {};
        d3.keys(country.production).forEach(function(k) {
            country.productionCo2Intensities[k] = co2eq_parameters.footprintOf(
                k, country.countryCode);
        })
    });
    d3.values(exchanges).forEach(function(exchange) {
        exchange.co2intensity = countries[exchange.countryCodes[exchange.netFlow > 0 ? 0 : 1]].co2intensity;
    });
}
exports.elementQuery = function (keyName, keyValue, minDate, maxDate) {
    var query = { datetime: exports.rangeQuery(minDate, maxDate) };
    query[keyName] = keyValue
    return query;
}
exports.rangeQuery = function (minDate, maxDate) {
    var query = { };
    if (minDate) query['$gte'] = minDate;
    if (maxDate) query['$lte'] = maxDate;
    return query;
}
exports.queryElements = function (keyName, keyValues, collection, minDate, maxDate, callback) {
    tasks = {};
    keyValues.forEach(function(k) {
        tasks[k] = function(callback) { 
            return collection.findOne(
                exports.elementQuery(keyName, k, minDate, maxDate),
                { sort: [['datetime', -1]] },
                callback);
        };
    });
    return async.parallel(tasks, callback);
}
exports.queryLastValuesBeforeDatetime = function (datetime, callback) {
    var minDate = (moment(datetime) || moment.utc()).subtract(24, 'hours').toDate();
    var maxDate = datetime ? new Date(datetime) : undefined;
    // Get list of countries, exchanges, and prices in db
    return async.parallel([
        function(callback) {
            mongoProductionCollection.distinct('countryCode',
                {datetime: exports.rangeQuery(minDate, maxDate)}, callback);
        },
        function(callback) {
            mongoExchangeCollection.distinct('sortedCountryCodes',
                {datetime: exports.rangeQuery(minDate, maxDate)}, callback);
        },
        function(callback) {
            mongoPriceCollection.distinct('countryCode',
                {datetime: exports.rangeQuery(minDate, maxDate)}, callback);
        },
    ], function(err, results) {
        if (err) return callback(err);
        productionCountryCodes = results[0]; // production keys
        sortedCountryCodes = results[1]; // exchange keys
        priceCountryCodes = results[2]; // price keys
        // Query productions + exchanges
        async.parallel([
            function(callback) {
                return exports.queryElements('countryCode', productionCountryCodes,
                    mongoProductionCollection, minDate, maxDate, callback);
            },
            function(callback) {
                return exports.queryElements('sortedCountryCodes', sortedCountryCodes,
                    mongoExchangeCollection, minDate, maxDate, callback);
            },
            function(callback) {
                return exports.queryElements('countryCode', priceCountryCodes,
                    mongoPriceCollection, minDate, maxDate, callback);
            },
        ], function(err, results) {
            if (err) return callback(err);
            countries = results[0];
            exchanges = results[1];
            prices = results[2];
            // This can crash, so we to try/catch
            try {
                result = processDatabaseResults(countries, exchanges, prices);
            } catch(err) {
                callback(err);
            }
            callback(err, result);
        });
    });
}
exports.queryLastValues = function (callback) {
    return exports.queryLastValuesBeforeDatetime(undefined, callback);
}
function queryGfsAt(key, refTime, targetTime, callback) {
    refTime = moment(refTime).toDate();
    targetTime = moment(targetTime).toDate();
    return mongoGfsCollection.findOne({ key, refTime, targetTime }, callback);
}
function queryLastGfsBefore(key, datetime, callback) {
    return mongoGfsCollection.findOne(
        { key, targetTime: exports.rangeQuery(
            moment(datetime).subtract(2, 'hours').toDate(), datetime) },
        { sort: [['refTime', -1], ['targetTime', -1]] },
        callback);
}
function queryLastGfsAfter(key, datetime, callback) {
    return mongoGfsCollection.findOne(
        { key, targetTime: exports.rangeQuery(datetime,
            moment(datetime).add(2, 'hours').toDate()) },
        { sort: [['refTime', -1], ['targetTime', 1]] },
        callback);
}
function decompressGfs(obj, callback) {
    if (!obj) return callback(null, null);
    return snappy.uncompress(obj, { asBuffer: true }, function (err, obj) {
        if (err) return callback(err);
        return callback(err, JSON.parse(obj));
    });
}
function queryForecasts(key, datetime, callback) {
    function fetchBefore(callback) {
        return queryLastGfsBefore(key, now, callback);
    };
    function fetchAfter(callback) {
        return queryLastGfsAfter(key, now, callback);
    };
    return async.parallel([fetchBefore, fetchAfter], callback);
}
function getParsedForecasts(key, datetime, useCache, callback) {
    // Fetch two forecasts, using the cache if possible
    var kb = key + '_before';
    var ka = key + '_after';
    function getCache(key, useCache, callback) {
        if (!useCache) return callback(null, {});
        return memcachedClient.getMulti([kb, ka], callback);
    }
    getCache(key, useCache, function (err, data) {
        if (err) {
            return callback(err);
        } else if (!data || !data[kb] || !data[ka]) {
            // Nothing in cache, proceed as planned
            return queryForecasts(key, datetime, function(err, objs) {
                if (err) return callback(err);
                if (!objs[0] || !objs[1]) return callback(null, null);
                // Store raw (compressed) values in cache
                if (useCache) {
                    var lifetime = parseInt(
                        (moment(objs[1]['targetTime']).toDate().getTime() - (new Date()).getTime()) / 1000.0);
                    memcachedClient.set(kb, objs[0]['data'].buffer, lifetime, handleError);
                    memcachedClient.set(ka, objs[1]['data'].buffer, lifetime, handleError);
                }
                // Decompress
                return async.parallel([
                    function(callback) { return decompressGfs(objs[0]['data'].buffer, callback); },
                    function(callback) { return decompressGfs(objs[1]['data'].buffer, callback); }
                ], function(err, objs) {
                    if (err) return callback(err);
                    // Return to sender
                    return callback(null, {'forecasts': objs, 'cached': false});
                });
            })
        } else {
            // Decompress data, to be able to reconstruct a database object
            return async.parallel([
                function(callback) { return decompressGfs(data[kb], callback); },
                function(callback) { return decompressGfs(data[ka], callback); }
            ], function(err, objs) {
                if (err) return callback(err);
                // Reconstruct database object and return to sender
                return callback(null, {'forecasts': objs, 'cached': true});
            });
        }
    });
}
