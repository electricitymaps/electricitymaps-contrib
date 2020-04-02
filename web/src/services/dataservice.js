/* eslint-disable */
// TODO: remove once refactored

import { sha256 } from 'js-sha256';

var Cookies = require('js-cookie');
const d3 = Object.assign(
  {},
  require('d3-queue'),
  require('d3-request'),
);
var moment = require('moment');
const { TIMESCALE } = require('../helpers/constants');

// API
function protectedJsonRequest(endpoint, path, callback) {
  const now = new Date().getTime();
  const tk = (endpoint.indexOf('localhost') !== -1)
    ? 'development'
    : ELECTRICITYMAP_PUBLIC_TOKEN;
  const signature = sha256(tk + path + now);
  const req = d3.json(endpoint + path)
    .header('electricitymap-token', Cookies.get('electricitymap-token'))
    .header('x-request-timestamp', now)
    .header('x-signature', signature);

  return req.get(null, callback);
}

// GFS Parameters
var GFS_STEP_ORIGIN  = 6; // hours
var GFS_STEP_HORIZON = 1; // hours
const fetchForecast = function(endpoint, key, refTime, targetTime, tryEarlierRefTime, tryModuloBefore, tryModuloAfter, callback) {
  refTime = moment(refTime);
  targetTime = moment(targetTime);
  return protectedJsonRequest(endpoint, '/v3/gfs/' + key + '?' +
    'refTime=' + refTime.toISOString() + '&' +
    'targetTime=' + targetTime.toISOString(), function(err, obj) {
            // Here we should first allow to fetch at % 3 if
            // we're looking at historical data, as we couldn't re-fetch everything.
            if (err && tryModuloBefore) {
                // Fetch at % 3 under
                return fetchForecast(endpoint, key, refTime,
                  targetTime.hour(
                    Math.floor(targetTime.hour() / 3) * 3
                    ), tryEarlierRefTime, false, false, callback);
              }
              else if (err && tryModuloAfter) {
                // Fetch at % 3 after
                return fetchForecast(endpoint, key, refTime,
                  targetTime.hour(
                    Math.ceil(targetTime.hour() / 3) * 3
                    ), tryEarlierRefTime, false, false, callback);
              }
              else if (err && tryEarlierRefTime)
                return fetchForecast(endpoint, key, refTime.subtract(GFS_STEP_ORIGIN, 'hour'),
                  targetTime, false, tryModuloBefore, tryModuloAfter, callback);
              else
                return callback(err, obj);
            });
}
const getGfsTargetTimeBefore = function(datetime) {
  var horizon = moment(datetime).utc().startOf('hour');
  while ((horizon.hour() % GFS_STEP_HORIZON) != 0)
    horizon.subtract(1, 'hour');
  return horizon;
}
const getGfsRefTimeForTarget = function(datetime) {
  // Warning: solar will not be available at horizon 0
  // so always do at least horizon 1
  var origin = moment(datetime).subtract(1, 'hour');
  while ((origin.hour() % GFS_STEP_ORIGIN) != 0)
    origin.subtract(1, 'hour');
  return origin;
}
const fetchGfs = function(endpoint, key, datetime, callback) {
  var targetTimeBefore = getGfsTargetTimeBefore(datetime);
  var targetTimeAfter = moment(targetTimeBefore).add(GFS_STEP_HORIZON, 'hour');
  // Note: d3.queue runs tasks in parallel
  var tryModulo = false;//window.customDate != undefined;
  return d3.queue()
  .defer(fetchForecast, endpoint, key, getGfsRefTimeForTarget(targetTimeBefore), targetTimeBefore, true, tryModulo, false)
  .defer(fetchForecast, endpoint, key, getGfsRefTimeForTarget(targetTimeAfter), targetTimeAfter, true, false, tryModulo)
  .await(function(err, before, after) {
    if (err) return callback(err, null);
    return callback(null, { forecasts: [before.data, after.data] });
  });
}
const fetchNothing = function(callback) {
  return callback(null, null);
}
const fetchState = function(endpoint, datetime, timescale, callback) {
  var path = '/v3/state' + (datetime ? '?datetime=' + datetime : '');
  if (timescale !== TIMESCALE.LIVE) {
    path += `?timescale=${timescale}_${moment().startOf('month').subtract(1, 'month').format('YYYYMM')}`;
  }
  return protectedJsonRequest(endpoint, path, callback);
}
const fetchHistory = function(endpoint, zone_name, timescale, callback) {
  let path = `/v3/history?countryCode=${zone_name}`;
  if (timescale !== TIMESCALE.LIVE) {
    path += `&timescale=${timescale}`;
  }
  return protectedJsonRequest(endpoint, path, callback);
}

export {
  fetchForecast,
  getGfsTargetTimeBefore,
  getGfsRefTimeForTarget,
  fetchGfs,
  fetchNothing,
  fetchState,
  fetchHistory,
};
