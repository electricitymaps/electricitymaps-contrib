var isProduction = process.env.ENV === 'production';

console.log('Starting push_cache..');

// * Opbeat (must be the first thing started)
if (isProduction) {
    var opbeat = require('opbeat').start({
        appId: 'c36849e44e',
        organizationId: '093c53b0da9d43c4976cd0737fe0f2b1',
        secretToken: process.env['OPBEAT_SECRET']
    });
    app.use(opbeat.middleware.express())
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

    // Compute values for the last 24 hours, step 5min
    var now = moment();
    var before = moment(now).subtract(1, 'day');
    var dates = d3.timeMinute.every(5).range(before.toDate(), now.toDate());

    var tasks = dates.map(function(d) {
        return function (callback) {
            return db.queryLastValuesBeforeDatetime(d, callback)
        };
    });
    // Use a `series` call to avoid running out of memory
    console.log('Querying state history..');
    return async.series(tasks, function (err, objs) {
        if (err) {
            return handleError(err);
        }
        // Iterate for each country
        console.log('Pushing CO2 histories..');
        countryCodes = d3.keys(objs[objs.length - 1].countries);
        countryCodes.forEach(function (countryCode) {
            // Get a timeseries of CO2
            // and dedup by datetime
            var dict = {};
            objs.forEach(function (d) {
                var c = d.countries[countryCode];
                if (!c) return;
                dict[c.datetime] = c;
            });
            var ts = d3.values(dict)
                .sort(function (x, y) { return d3.ascending(x.datetime, y.datetime); });
            // Push to cache
            db.setCache(
                CACHE_KEY_PREFIX_HISTORY_CO2 + countryCode,
                ts, 24 * 3600,
                function (err) {
                    if (err) handleError(err);
                });
        });
        // done
        console.log('Done.')
        process.exit();
    });

});
