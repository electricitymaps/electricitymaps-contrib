/* eslint-disable */
// TODO: remove once refactored

import * as d3 from 'd3-format';
import { TIME } from './constants';
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
  if (d >= 1)
    // a ton or more
    return d3.format('.' + numDigits + 's')(d) + 't ' + translation.translate('ofCO2eqPerMinute');
  else return d3.format('.' + numDigits + 's')(d * 1e6) + 'g ' + translation.translate('ofCO2eqPerMinute');
};
const scalePower = function (maxPower) {
  // Assume MW input
  if (maxPower < 1)
    return {
      unit: 'kW',
      formattingFactor: 1e-3,
    };
  if (maxPower < 1e3)
    return {
      unit: 'MW',
      formattingFactor: 1,
    };
  else
    return {
      unit: 'GW',
      formattingFactor: 1e3,
    };
};

const formatDate = function (date, lang, time) {
  if (!date) return '';

  switch (time) {
    case TIME.DAILY:
      return new Intl.DateTimeFormat(lang, { dateStyle: 'long' }).format(date);
    case TIME.HOURLY:
      return new Intl.DateTimeFormat(lang, { dateStyle: 'long', timeStyle: 'short' }).format(date);
  }
};

const getLocaleUnit = (dateUnit, lang) =>
  new Intl.NumberFormat(lang, {
    style: 'unit',
    unit: dateUnit,
    unitDisplay: 'long',
  })
    .formatToParts(1)
    .filter((x) => x.type === 'unit')[0].value;

const getLocaleNumberFormat = (lang, { unit, unitDisplay, range }) =>
  new Intl.NumberFormat(lang, {
    style: 'unit',
    unit: unit,
    unitDisplay: unitDisplay || 'long',
  }).format(range);

const formatTimeRange = (lang, timeAggregate) => {
  // Note that not all browsers fully support all languages
  switch (timeAggregate) {
    case TIME.HOURLY:
      return getLocaleNumberFormat(lang, { unit: 'hour', range: 24 });
    case TIME.DAILY:
      return getLocaleUnit('month', lang);
    case TIME.MONTHLY:
      return getLocaleUnit('year', lang);
    case TIME.YEARLY:
      return getLocaleNumberFormat(lang, { unit: 'year', range: 5 });
    default:
      break;
  }
};

const formatDateTick = function (date, lang, time) {
  if (!date) return '';

  switch (time) {
    case TIME.DAILY:
      return new Intl.DateTimeFormat(lang, { month: 'long', day: 'numeric' }).format(date);
    case TIME.HOURLY:
      return new Intl.DateTimeFormat(lang, { timeStyle: 'short' }).format(date);
  }
};

export { formatPower, formatCo2, scalePower, formatDate, formatTimeRange, formatDateTick };
