import * as d3 from 'd3-format';
import { TimeAverages } from './constants';
import { EnergyUnits } from './units';

const DEFAULT_NUM_DIGITS = 2;

function addSpaceBetweenNumberAndUnit(inputString: string) {
  // Use a regular expression to add a space between the number and unit
  return inputString.replace(/([A-Za-z])/, ' $1');
}

export const formatPower = function (
  d: number,
  numberDigits: number = DEFAULT_NUM_DIGITS
) {
  // Assume MW input
  if (d == undefined || Number.isNaN(d)) {
    return d;
  }
  const significantFigures = d.toString().length > 1 ? numberDigits : 1;
  const power =
    d < 1e9
      ? d3.format(`.${significantFigures}s`)(d * 1e6) + 'W'
      : d3.format(`.${significantFigures}r`)(d / 1e6) + 'TW';
  return addSpaceBetweenNumberAndUnit(power);
};

export const formatEnergy = function (
  d: number,
  numberDigits: number = DEFAULT_NUM_DIGITS
) {
  const power = formatPower(d, numberDigits);
  // Assume MW input
  if (power == undefined || Number.isNaN(power)) {
    return power;
  }
  return power + 'h';
};

export const formatCo2 = function (grams: number, valueToMatch?: number): string {
  // Validate input
  if (grams == null || Number.isNaN(grams)) {
    return '?';
  }

  // Ensure both numbers are at the same scale
  const checkAgainst = valueToMatch ?? grams;

  //Values less than 1Mt
  if (Math.round(checkAgainst) < 1e9) {
    let decimals = grams < 1 ? 2 : 1;
    // Remove decimals for large values
    if (grams > 1_000_000) {
      decimals = 2;
    }
    if (checkAgainst < 1e6) {
      return addSpaceBetweenNumberAndUnit(`${d3.format(`,.${decimals}~s`)(grams)}g`);
    }

    return addSpaceBetweenNumberAndUnit(`${d3.format(`,.${decimals}~r`)(grams / 1e6)}t`);
  }
  // tonnes or above with significant figures as a default
  return addSpaceBetweenNumberAndUnit(`${d3.format(',.2~s')(grams / 1e6)}t`);
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
