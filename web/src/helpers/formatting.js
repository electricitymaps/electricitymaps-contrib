/* eslint-disable */
// TODO: remove once refactored

import * as d3 from 'd3-format';
import * as translation from './translation';

const formatPower = function (d, numDigits) {
  // Assume MW input
  if (d == null || d === NaN) return d;
  if (numDigits == null) numDigits = 3;
  return d3.format('.' + numDigits + 's')(d * 1e6) + 'W';
};
const formatCo2 = function (d, numDigits) {
  // Assume gCO₂ / h input
  d /= 60; // Convert to gCO₂ / min
  d /= 1e6; // Convert to tCO₂ / min
  if (d == null || d === NaN) return d;
  if (numDigits == null) numDigits = 3;
  if (d >= 1) // a ton or more
    return d3.format('.' + numDigits + 's')(d) + 't ' + translation.translate('ofCO2eqPerMinute');
  else
    return d3.format('.' + numDigits + 's')(d * 1e6) + 'g ' + translation.translate('ofCO2eqPerMinute');
};
const scalePower = function (maxPower) {
  // Assume MW input
  if (maxPower < 1)
    return {
      unit: "kW",
      formattingFactor: 1e-3
    }
  if (maxPower < 1e3)
    return {
      unit: "MW",
      formattingFactor: 1
    }
  else return {
      unit: "GW",
      formattingFactor: 1e3
    }
};

const formatHourlyDate = function (date, lang) {
  // formats date object to readable date
  if (!date) return '';
  return new Intl.DateTimeFormat(lang, {dateStyle: 'long', timeStyle: 'short' }).format(date);
};

export {
  formatPower,
  formatCo2,
  scalePower,
  formatHourlyDate
};