'use strict';

var d3 = require('d3-format');
var translation = require('./translation');

var co2Sub = module.exports.co2Sub = function (str) {
  return str.replace('CO2', 'CO<span class="sub">2</span>');
};
module.exports.formatPower = function (d, numDigits) {
  // Assume MW input
  if (d == null || d === NaN) return d;
  if (numDigits == null) numDigits = 3;
  return d3.format('.' + numDigits + 's')(d * 1e6) + 'W';
};
module.exports.formatCo2 = function (d, numDigits) {
  // Assume gCO2 / h input
  d /= 60; // Convert to gCO2 / min
  d /= 1e6; // Convert to tCO2 / min
  if (d == null || d === NaN) return d;
  if (numDigits == null) numDigits = 3;
  if (d >= 1) // a ton or more
    return d3.format('.' + numDigits + 's')(d) + 't ' + co2Sub(translation.translate('ofCO2eqPerMinute'));
  else
    return d3.format('.' + numDigits + 's')(d * 1e6) + 'g ' + co2Sub(translation.translate('ofCO2eqPerMinute'));
};
