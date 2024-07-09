import * as d3 from 'd3-format';

import { TimeAverages } from './constants';
import { EnergyUnits, PowerUnits } from './units';

const DEFAULT_NUM_DIGITS = 3;

function addSpaceBetweenNumberAndUnit(inputString: string) {
  // Use a regular expression to add a space between the number and unit
  return inputString.replace(/([A-Za-z])/, ' $1');
}

export const formatPower = (d: number, numberDigits: number = DEFAULT_NUM_DIGITS) => {
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

export const formatEnergy = (d: number, numberDigits: number = DEFAULT_NUM_DIGITS) => {
  const power = formatPower(d, numberDigits);
  // Assume MW input
  if (power == undefined || Number.isNaN(power)) {
    return power;
  }
  return power + 'h';
};

export const formatCo2 = (grams: number, valueToMatch?: number): string => {
  // Validate input
  if (grams == null || Number.isNaN(grams)) {
    return '?';
  }

  // Ensure both numbers are at the same scale
  const checkAgainst = valueToMatch ?? grams;

  //Values less than 1Mt
  if (Math.abs(Math.round(checkAgainst)) < 1e9) {
    let decimals = grams < 1 ? 2 : 1;
    // Remove decimals for large values
    if (grams > 1_000_000) {
      decimals = 2;
    }
    if (Math.abs(checkAgainst) < 1e6) {
      return addSpaceBetweenNumberAndUnit(`${d3.format(`,.${decimals}~s`)(grams)}g`);
    }

    return addSpaceBetweenNumberAndUnit(`${d3.format(`,.${decimals}~r`)(grams / 1e6)}t`);
  }
  // tonnes or above with significant figures as a default
  return addSpaceBetweenNumberAndUnit(`${d3.format(',.3~s')(grams / 1e6)}t`);
};

const scalePower = (maxPower: number | undefined, isPower = false) => {
  // Assume MW input
  if (maxPower == undefined) {
    return {
      unit: '?',
      formattingFactor: 1e3,
    };
  }

  const thresholds: [number, EnergyUnits | PowerUnits][] = isPower
    ? [
        [1e9, PowerUnits.PETAWATTS],
        [1e6, PowerUnits.TERAWATTS],
        [1e3, PowerUnits.GIGAWATTS],
        [1, PowerUnits.MEGAWATTS],
        [1e-3, PowerUnits.KILOWATTS],
      ]
    : [
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

export const getDateTimeFormatOptions = (
  timeAverage: TimeAverages
): Intl.DateTimeFormatOptions => {
  switch (timeAverage) {
    case TimeAverages.HOURLY: {
      return {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        timeZoneName: 'short',
      };
    }
    case TimeAverages.DAILY: {
      return {
        dateStyle: 'long',
        timeZone: 'UTC',
      };
    }
    case TimeAverages.MONTHLY: {
      return {
        month: 'long',
        year: 'numeric',
        timeZone: 'UTC',
      };
    }
    case TimeAverages.YEARLY: {
      return {
        year: 'numeric',
        timeZone: 'UTC',
      };
    }
    default: {
      console.error(`${timeAverage} is not implemented`);
      return {};
    }
  }
};

const formatDate = (date: Date, lang: string, timeAverage: TimeAverages) => {
  if (!isValidDate(date) || !timeAverage) {
    return '';
  }
  return new Intl.DateTimeFormat(lang, getDateTimeFormatOptions(timeAverage)).format(
    date
  );
};

const formatDateTick = (date: Date, lang: string, timeAggregate: TimeAverages) => {
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

export { formatDataSources, formatDate, formatDateTick, scalePower };
