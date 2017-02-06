var isProduction = process.env.ENV === 'production';

console.log('Starting push_cache..');

// * Opbeat (must be the first thing started)
if (isProduction) {
    var opbeat = require('opbeat').start({
        appId: 'c36849e44e',
        organizationId: '093c53b0da9d43c4976cd0737fe0f2b1',
        secretToken: process.env['OPBEAT_SECRET']
    });
}
function handleError(err) {
    if (!err) return;
    if (opbeat) opbeat.captureError(err);
    console.error(err);
}

// Require
var async = require('async');
var d3 = require('d3');
var moment = require('moment');

// Custom modules
global.__base = __dirname;
var db = require('../shared/database');

db.connect(function (err, _) {
    if (err) throw (err);
    // cache key accessors
    var CACHE_KEY_PREFIX_HISTORY_CO2 = 'HISTORY_';

    var now = moment();
    var before = moment(now).subtract(1, 'day');
    var dates = d3.timeMinute.every(15).range(before.toDate(), now.toDate());

    var queryTasks = dates.map(function(d) {
        return function (callback) {
            return db.queryLastValuesBeforeDatetimeWithExpiration(d, 2 * 60, callback)
        };
    });
    console.log('Querying state history..');
    return async.parallel(queryTasks, function (err, objs) {
        if (err) {
            return handleError(err);
        }
        // Iterate for each country
        console.log('Pushing histories..');
        countryCodes = d3.keys(objs[objs.length - 1].countries);
        var insertTasks = countryCodes.map(function (countryCode) {
            // The datetime used is the datetime of the query
            // because we query the best known state of the whole grid
            // not just that specific country
            var ts = objs.map(function (d, i) {
                var country = d.countries[countryCode] || {};
                // Add a marker representing the query time
                country.stateDatetime = dates[i];
                return country;
            });
            // Push to cache
            return function (callback) {
                db.setCache(
                    CACHE_KEY_PREFIX_HISTORY_CO2 + countryCode,
                    ts, 24 * 3600,
                    callback);
            }
        });
        async.parallel(insertTasks, function (err) {
            // done
            console.log('..done')
            process.exit();
        });
    });
});
