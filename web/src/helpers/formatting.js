import * as d3 from 'd3-format';
import { TIME } from './constants';
import * as translation from './translation';

const DEFAULT_NUM_DIGITS = 3;

const formatPower = function (d, numDigits = DEFAULT_NUM_DIGITS) {
  // Assume MW input
  if (d == null || isNaN(d)) {
    return d;
  }
  return `${d3.format(`.${numDigits}s`)(d * 1e6)}W`;
};
const formatCo2 = function (d, numDigits = DEFAULT_NUM_DIGITS) {
  let value = d;
  // Assume gCO₂ / h input
  value /= 60; // Convert to gCO₂ / min
  value /= 1e6; // Convert to tCO₂ / min
  if (d == null || isNaN(d)) {
    return d;
  }

  if (d >= 1) {
    // a ton or more
    return `${d3.format(`.${numDigits}s`)(value)}t ${translation.translate('ofCO2eqPerMinute')}`;
  } else {
    return `${d3.format(`.${numDigits}s`)(value * 1e6)}g ${translation.translate('ofCO2eqPerMinute')}`;
  }
};
const scalePower = function (maxPower) {
  // Assume MW input
  if (maxPower < 1) {
    return {
      unit: 'kW',
      formattingFactor: 1e-3,
    };
  }
  if (maxPower < 1e3) {
    return {
      unit: 'MW',
      formattingFactor: 1,
    };
  } else {
    return {
      unit: 'GW',
      formattingFactor: 1e3,
    };
  }
};

const formatDate = function (date, lang, time) {
  if (!isValidDate(date) || !time) {
    return '';
  }

  switch (time) {
    case TIME.HOURLY:
      return new Intl.DateTimeFormat(lang, { dateStyle: 'long', timeStyle: 'short' }).format(date);
    case TIME.DAILY:
      return new Intl.DateTimeFormat(lang, { dateStyle: 'long' }).format(date);
    case TIME.MONTHLY:
      return new Intl.DateTimeFormat(lang, { month: 'long', year: 'numeric' }).format(date);
    case TIME.YEARLY:
      return new Intl.DateTimeFormat(lang, { year: 'numeric' }).format(date);
    default:
      console.error(`${time} is not implemented`);
      return '';
  }
};

const getLocaleNumberFormat = (lang, { unit, unitDisplay, range }) =>
  new Intl.NumberFormat(lang, {
    style: 'unit',
    unit,
    unitDisplay: unitDisplay || 'long',
  }).format(range);

const formatTimeRange = (lang, timeAggregate) => {
  // Note that not all browsers fully support all languages
  switch (timeAggregate) {
    case TIME.HOURLY:
      return getLocaleNumberFormat(lang, { unit: 'hour', range: 24 });
    case TIME.DAILY:
      return getLocaleNumberFormat(lang, { unit: 'day', range: 30 });
    case TIME.MONTHLY:
      return getLocaleNumberFormat(lang, { unit: 'month', range: 12 });
    case TIME.YEARLY:
      return getLocaleNumberFormat(lang, { unit: 'year', range: 5 });
    default:
      console.error(`${timeAggregate} is not implemented`);
      return '';
  }
};

const formatDateTick = function (date, lang, timeAggregate) {
  if (!isValidDate(date) || !timeAggregate) {
    return '';
  }

  switch (timeAggregate) {
    case TIME.HOURLY:
      return new Intl.DateTimeFormat(lang, { timeStyle: 'short' }).format(date);
    case TIME.DAILY:
      return new Intl.DateTimeFormat(lang, { month: 'short', day: 'numeric' }).format(date);
    case TIME.MONTHLY:
      return new Intl.DateTimeFormat(lang, { month: 'short' }).format(date);
    case TIME.YEARLY:
      return new Intl.DateTimeFormat(lang, { year: 'numeric' }).format(date);
    default:
      console.error(`${timeAggregate} is not implemented`);
      return '';
  }
};

function isValidDate(date) {
  if (!date || !(date instanceof Date)) {
    return false;
  }

  if (!date.getTime() || date.getTime() <= 1) {
    return false;
  }

  return true;
}
/**
 * @param {string[]} dataSources - array of data sources.
 * @param {string} language - ISO 639-1 language code (`en`) or ISO 639-1 language code + ISO 3166-1 alpha-2 country code (`en-GB`).
 * @returns {string} formatted string of data sources.
 */
function formatDataSources(dataSources, language) {
  if (typeof Intl.ListFormat !== 'undefined') {
    return new Intl.ListFormat(language, { style: 'long', type: 'conjunction' }).format(dataSources);
  } else {
    return dataSources.join(', ');
  }
}

export { formatPower, formatCo2, scalePower, formatDate, formatTimeRange, formatDateTick, formatDataSources };
