import * as d3 from 'd3-format';
import { TimeAverages } from './constants';
import { EnergyUnits } from './units';

const DEFAULT_NUM_DIGITS = 2;

export const formatPower = function (
  d: number,
  numberDigits: number = DEFAULT_NUM_DIGITS
) {
  // Assume MW input
  if (d == undefined || Number.isNaN(d)) {
    return d;
  }
  const power = `${d3.format(`.${numberDigits}s`)(d * 1e6)}Wh` //Add a space between the number and the unit
    .replace(/([A-Za-z])/, ' $1')
    .trim();
  return power;
};

export const formatCo2 = function (gramPerHour: number, valueToMatch?: number) {
  if (gramPerHour == undefined || Number.isNaN(gramPerHour)) {
    return gramPerHour;
  }

  // Assume gCO₂ / h input
  let value = gramPerHour;
  value /= 60; // Convert to gCO₂ / min
  value /= 1e6; // Convert to tCO₂ / min

  // Ensure both numbers are at the same scale
  const checkAgainst = valueToMatch ? valueToMatch / 1e6 : value;

  // grams and kilograms
  if (checkAgainst < 1) {
    return `${d3.format(`,.0~s`)(value * 1e6)}g`;
  }

  // tons
  if (Math.round(checkAgainst) < 1e5) {
    const decimals = value < 1 ? 2 : 1;
    return `${d3.format(`,.${decimals}~f`)(value)}t`;
  }

  // Hundred thousands of tons
  if (Math.round(checkAgainst) < 1e6) {
    return `${d3.format(`,.1~f`)(value / 1e6)}Mt`;
  }

  // megatons or above
  return `${d3.format(`,.2~s`)(value)}t`;
};

const scalePower = function (maxPower: number | undefined) {
  // Assume MW input
  if (maxPower == undefined) {
    return {
      unit: '?',
      formattingFactor: 1e3,
    };
  }

  const thresholds: [number, EnergyUnits][] = [
    [1e9, EnergyUnits.PETAWATT_HOURS],
    [1e6, EnergyUnits.TERAWATT_HOURS],
    [1e3, EnergyUnits.GIGAWATT_HOURS],
    [1, EnergyUnits.MEGAWATT_HOURS],
    [1e-3, EnergyUnits.KILOWATT_HOURS],
  ];

  // Use absolute value to handle negative values
  const value = Math.abs(maxPower);

  for (const [threshold, unit] of thresholds) {
    if (value >= threshold) {
      return {
        unit,
        formattingFactor: threshold,
      };
    }
  }

  // Fallback if none of the thresholds are met
  return {
    unit: EnergyUnits.PETAWATT_HOURS,
    formattingFactor: 1e9,
  };
};

const formatDate = function (date: Date, lang: string, time: string) {
  if (!isValidDate(date) || !time) {
    return '';
  }

  switch (time) {
    case TimeAverages.HOURLY: {
      return new Intl.DateTimeFormat(lang, {
        dateStyle: 'medium',
        timeStyle: 'short',
      }).format(date);
    }
    // Instantiate below DateTimeFormat objects using UTC to avoid displaying
    // misleading time slider labels for users in UTC-negative offset timezones
    case TimeAverages.DAILY: {
      return new Intl.DateTimeFormat(lang, {
        dateStyle: 'long',
        timeZone: 'UTC',
      }).format(date);
    }
    case TimeAverages.MONTHLY: {
      return new Intl.DateTimeFormat(lang, {
        month: 'long',
        year: 'numeric',
        timeZone: 'UTC',
      }).format(date);
    }
    case TimeAverages.YEARLY: {
      return new Intl.DateTimeFormat(lang, {
        year: 'numeric',
        timeZone: 'UTC',
      }).format(date);
    }
    default: {
      console.error(`${time} is not implemented`);
      return '';
    }
  }
};

const getLocaleNumberFormat = (lang: string, { unit, unitDisplay, range }: any) => {
  try {
    return new Intl.NumberFormat(lang, {
      style: 'unit',
      unit,
      unitDisplay: unitDisplay || 'long',
    }).format(range);
  } catch {
    // As Intl.NumberFormat with custom 'unit' is not supported in all browsers, we fallback to
    // a simple English based implementation
    const plural = range === 1 ? '' : 's';
    return `${range} ${unit}${plural}`;
  }
};

const formatTimeRange = (lang: string, timeAggregate: TimeAverages) => {
  // Note that not all browsers fully support all languages
  switch (timeAggregate) {
    case TimeAverages.HOURLY: {
      return getLocaleNumberFormat(lang, { unit: 'hour', range: 24 });
    }
    case TimeAverages.DAILY: {
      return getLocaleNumberFormat(lang, { unit: 'day', range: 30 });
    }
    case TimeAverages.MONTHLY: {
      return getLocaleNumberFormat(lang, { unit: 'month', range: 12 });
    }
    case TimeAverages.YEARLY: {
      return getLocaleNumberFormat(lang, {
        unit: 'year',
        range: new Date().getUTCFullYear() - 2017,
      });
    }
    default: {
      console.error(`${timeAggregate} is not implemented`);
      return '';
    }
  }
};

const formatDateTick = function (date: Date, lang: string, timeAggregate: TimeAverages) {
  if (!isValidDate(date) || !timeAggregate) {
    return '';
  }

  switch (timeAggregate) {
    case TimeAverages.HOURLY: {
      return new Intl.DateTimeFormat(lang, {
        timeStyle: 'short',
      }).format(date);
    }
    // Instantiate below DateTimeFormat objects using UTC to avoid displaying
    // misleading time slider labels for users in UTC-negative offset timezones
    case TimeAverages.DAILY: {
      return new Intl.DateTimeFormat(lang, {
        month: 'short',
        day: 'numeric',
        timeZone: 'UTC',
      }).format(date);
    }
    case TimeAverages.MONTHLY: {
      return lang === 'et'
        ? new Intl.DateTimeFormat(lang, {
            month: 'short',
            day: 'numeric',
            timeZone: 'UTC',
          })
            .formatToParts(date)
            .find((part) => part.type === 'month')?.value
        : new Intl.DateTimeFormat(lang, {
            month: 'short',
            timeZone: 'UTC',
          }).format(date);
    }
    case TimeAverages.YEARLY: {
      return new Intl.DateTimeFormat(lang, {
        year: 'numeric',
        timeZone: 'UTC',
      }).format(date);
    }
    default: {
      console.error(`${timeAggregate} is not implemented`);
      return '';
    }
  }
};

function isValidDate(date: Date) {
  if (!date || !(date instanceof Date)) {
    return false;
  }

  if (!date?.getTime() || date?.getTime() <= 1) {
    return false;
  }

  return true;
}
/**
 * @param {string[]} dataSources - array of data sources.
 * @param {string} language - ISO 639-1 language code (`en`) or ISO 639-1 language code + ISO 3166-1 alpha-2 country code (`en-GB`).
 * @returns {string} formatted string of data sources.
 */
function formatDataSources(dataSources: string[], language: string) {
  return Intl.ListFormat === undefined
    ? dataSources.join(', ')
    : new Intl.ListFormat(language, { style: 'long', type: 'conjunction' }).format(
        dataSources
      );
}

export { formatDataSources, formatDate, formatDateTick, formatTimeRange, scalePower };
