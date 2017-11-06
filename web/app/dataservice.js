var exports = module.exports = {};

var forge = require('node-forge');
var Cookies = require('js-cookie');
var d3 = require('d3');
var moment = require('moment');

// API
function protectedJsonRequest(endpoint, path, callback) {
    // Do not pass headers in development
    var t = new Date().getTime();
    var md = forge.md.sha256.create();
    var s = md.update(ELECTRICITYMAP_PUBLIC_TOKEN + path + t).digest().toHex();
    var req = d3.json(endpoint + path);
    if (window.useRemoteEndpoint) {
        req = req.header('electricitymap-token', Cookies.get('electricitymap-token'))
            .header('x-request-timestamp', t)
            .header('x-signature', s)
    }
    return req.get(null, callback);
}

// GFS Parameters
var GFS_STEP_ORIGIN  = 6; // hours
var GFS_STEP_HORIZON = 1; // hours
var fetchForecast = exports.fetchForecast = function(endpoint, key, refTime, targetTime, tryEarlierRefTime, callback) {
    refTime = moment(refTime);
    targetTime = moment(targetTime);
    return protectedJsonRequest(endpoint, '/v3/gfs/' + key + '?' +
        'refTime=' + refTime.toISOString() + '&' +
        'targetTime=' + targetTime.toISOString(), function(err, obj) {
            if (err && tryEarlierRefTime)
                return fetchForecast(endpoint, key, refTime.subtract(GFS_STEP_ORIGIN, 'hour'),
                    targetTime, false, callback);
            else
                return callback(err, obj);
        });
}
var getGfsTargetTimeBefore = exports.getGfsTargetTimeBefore = function(datetime) {
    var horizon = moment(datetime).utc().startOf('hour');
    while ((horizon.hour() % GFS_STEP_HORIZON) != 0)
        horizon.subtract(1, 'hour');
    return horizon;
}
var getGfsRefTimeForTarget = exports.getGfsRefTimeForTarget = function(datetime) {
    // Warning: solar will not be available at horizon 0
    // so always do at least horizon 1
    var origin = moment(datetime).subtract(1, 'hour');
    while ((origin.hour() % GFS_STEP_ORIGIN) != 0)
        origin.subtract(1, 'hour');
    return origin;
}
exports.fetchGfs = function(endpoint, key, datetime, callback) {
    var targetTimeBefore = getGfsTargetTimeBefore(datetime);
    var targetTimeAfter = moment(targetTimeBefore).add(GFS_STEP_HORIZON, 'hour');
    // Note: d3.queue runs tasks in parallel
    return d3.queue()
        .defer(fetchForecast, endpoint, key, getGfsRefTimeForTarget(targetTimeBefore), targetTimeBefore, true)
        .defer(fetchForecast, endpoint, key, getGfsRefTimeForTarget(targetTimeAfter), targetTimeAfter, true)
        .await(function(err, before, after) {
            if (err) return callback(err, null);
            return callback(null, { forecasts: [before.data, after.data] });
        });
}
exports.fetchNothing = function(callback) {
    return callback(null, null);
}
exports.fetchState = function(endpoint, datetime, callback) {
    var path = '/v3/state' + (datetime ? '?datetime=' + datetime : '');
    return protectedJsonRequest(endpoint, path, callback);
}
exports.fetchHistory = function(endpoint, zone_name, callback) {
    var path = '/v3/history?countryCode=' + zone_name;
    return protectedJsonRequest(endpoint, path, callback);
}
