var exports = module.exports = {};

var Cookies = require('js-cookie');
var d3 = require('d3');
var moment = require('moment');

// GFS Parameters
var GFS_STEP_ORIGIN  = 6; // hours
var GFS_STEP_HORIZON = 1; // hours
var fetchForecast = exports.fetchForecast = function(endpoint, key, refTime, targetTime, tryEarlierRefTime, callback) {
    refTime = moment(refTime);
    targetTime = moment(targetTime);
    return d3.json(endpoint + '/v2/gfs/' + key + '?' + 
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
    return Q = d3.queue()
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
    return d3.json(endpoint + '/v1/state' + (datetime ? '?datetime=' + datetime : ''))
        .header('electricitymap-token', Cookies.get('electricitymap-token'))
        .get(null, callback);
}
