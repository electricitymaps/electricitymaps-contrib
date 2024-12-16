import { describe, expect, it, vi } from 'vitest';

import { TimeRange } from './constants';
import {
  formatCo2,
  formatDataSources,
  formatDate,
  formatDateTick,
  formatEnergy,
  formatPower,
  getDateTimeFormatOptions,
  scalePower,
} from './formatting';
import { EnergyUnits, PowerUnits } from './units';

describe('formatEnergy', () => {
  it('handles NaN input', () => {
    const actual = formatEnergy({ value: Number.NaN });
    const expected = Number.NaN;
    expect(actual).to.deep.eq(expected);
  });

  it('handles custom number of digits', () => {
    const actual = formatEnergy({ value: 1.234_567, numberDigits: 4 });
    const expected = '1.235 MWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles default number kWh', () => {
    const actual = formatEnergy({ value: 0.002_234_567 });
    const expected = '2.23 kWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles MWh', () => {
    const actual = formatEnergy({ value: 1.234_567 });
    const expected = '1.23 MWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles GWh', () => {
    const actual = formatEnergy({ value: 1222.234_567 });
    const expected = '1.22 GWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles TWh', () => {
    const actual = formatEnergy({ value: 1_222_000.234_567 });
    const expected = '1.22 TWh';
    expect(actual).to.deep.eq(expected);
  });

  it('Converts PWh to TWh', () => {
    const actual = formatEnergy({ value: 1_222_000_000.234_567 });
    const expected = '1220 TWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles zero input', () => {
    const actual = formatEnergy({ value: 0 });
    const expected = '0 Wh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles 1 input for number of digits', () => {
    const actual = formatEnergy({ value: 12_313, numberDigits: 1 });
    const expected = '10 GWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles 0 input for number of digits', () => {
    const actual = formatEnergy({ value: 12_313, numberDigits: 0 });
    const expected = '10 GWh';
    expect(actual).to.deep.eq(expected);
  });

  it('handles using same unit as total for W', () => {
    const actual = formatPower({ value: 0.000_05, total: 0.0006 });
    const expected = '50 W';
    expect(actual).to.deep.eq(expected);
  });

  it('handles using same unit as total for W with decimal', () => {
    const actual = formatPower({ value: 0.000_054_6, total: 0.0006 });
    const expected = '54.6 W';
    expect(actual).to.deep.eq(expected);
  });

  it('handles using same unit as total for kW', () => {
    const actual = formatPower({ value: 0.003, total: 0.05 });
    const expected = '3 kW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles using same unit as total for kW with decimal', () => {
    const actual = formatPower({ value: 0.000_05, total: 0.05 });
    const expected = '0.05 kW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles value and total being the same', () => {
    const actual = formatPower({ value: 0.05, total: 0.05 });
    const expected = '50 kW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles using same unit as total for MW', () => {
    const actual = formatPower({ value: 0.009, total: 30 });
    const expected = '0.009 MW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles using same unit as total for GW', () => {
    const actual = formatPower({ value: 6.5, total: 70_000 });
    const expected = '0.0065 GW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles using same unit as total for GW with value being small', () => {
    const actual = formatPower({ value: 0.000_05, total: 70_000 });
    const expected = '0.00000005 GW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles using same unit as total for GW with value being very small', () => {
    const actual = formatPower({ value: 0.000_000_05, total: 70_000 });
    const expected = '~0 W';
    expect(actual).to.deep.eq(expected);
  });

  it('handles using same unit as total for GW with value being 0', () => {
    const actual = formatPower({ value: 0, total: 70_000 });
    const expected = '0 W';
    expect(actual).to.deep.eq(expected);
  });

  it('handles using same unit as total for TW', () => {
    const actual = formatPower({ value: 45, total: 890_000_000 });
    const expected = '0.000045 TW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles using same unit as total for TW with small value', () => {
    const actual = formatPower({ value: 0.000_05, total: 890_000_000 });
    const expected = '0.00000000005 TW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles using same unit as total for TW with a precise number', () => {
    const actual = formatPower({ value: 42_059.836_85, total: 890_000_000 });
    const expected = '0.0421 TW';
    expect(actual).to.deep.eq(expected);
  });
});

describe('formatPower', () => {
  it('handles NaN input', () => {
    const actual = formatPower({ value: Number.NaN });
    const expected = Number.NaN;
    expect(actual).to.deep.eq(expected);
  });

  it('handles custom number of digits', () => {
    const actual = formatPower({ value: 1.234_567, numberDigits: 4 });
    const expected = '1.235 MW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles default number kW', () => {
    const actual = formatPower({ value: 0.002_234_567 });
    const expected = '2.23 kW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles MW', () => {
    const actual = formatPower({ value: 1.234_567 });
    const expected = '1.23 MW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles GW', () => {
    const actual = formatPower({ value: 1222.234_567 });
    const expected = '1.22 GW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles TW', () => {
    const actual = formatPower({ value: 1_222_000.234_567 });
    const expected = '1.22 TW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles zero input', () => {
    const actual = formatPower({ value: 0 });
    const expected = '0 W';
    expect(actual).to.deep.eq(expected);
  });

  it('handles 1 input for number of digits', () => {
    const actual = formatPower({ value: 12_313, numberDigits: 1 });
    const expected = '10 GW';
    expect(actual).to.deep.eq(expected);
  });

  it('handles 0 input for number of digits', () => {
    const actual = formatPower({ value: 12_313, numberDigits: 0 });
    const expected = '10 GW';
    expect(actual).to.deep.eq(expected);
  });
});

describe('formatCo2', () => {
  it('handles NaN input', () => {
    const actual = formatCo2({ value: Number.NaN });
    const expected = '?';
    expect(actual).to.deep.eq(expected);
  });
  it('handles undefined input', () => {
    const actual = formatCo2({ value: undefined as unknown as number });
    const expected = '?';
    expect(actual).to.deep.eq(expected);
  });
  it('handles null input', () => {
    const actual = formatCo2({ value: null as unknown as number });
    const expected = '?';
    expect(actual).to.deep.eq(expected);
  });
  it('handles grams', () => {
    const actual = formatCo2({ value: 20 });
    const expected = '20 g';
    expect(actual).to.deep.eq(expected);
  });
  it('handles kilograms', () => {
    const actual = formatCo2({ value: 1000 });
    const expected = '1 kg';
    expect(actual).to.deep.eq(expected);
  });
  it('handles tonnes', () => {
    const actual = formatCo2({ value: 1_000_000 });
    const expected = '1 t';
    expect(actual).to.deep.eq(expected);
  });

  it('uses same unit as another value would', () => {
    const actual = formatCo2({ value: 23_500, total: 2_350_000 });
    const expected = '0.0235 t';
    expect(actual).to.deep.eq(expected);
  });

  it('adds decimals if comparing with tonnes', () => {
    const actual = formatCo2({ value: 200_500, total: 2_350_000 });
    const expected = '0.201 t';
    expect(actual).to.deep.eq(expected);
  });
  it('adds decimals if comparing with large tonnes', () => {
    const actual = formatCo2({ value: 200_500, total: 992_350_000 });
    const expected = '0.201 t';
    expect(actual).to.deep.eq(expected);
  });
  it('handles real data value', () => {
    const actual = formatCo2({ value: 740_703_650 });
    const expected = '741 t';
    expect(actual).to.deep.eq(expected);
  });
  it('handles kilotonnes', () => {
    const actual = formatCo2({ value: 99_000_000_000 });
    const expected = '99 kt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles megatonnes', () => {
    const actual = formatCo2({ value: 99_000_000_000_000 });
    const expected = '99 Mt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles megatonnes close to 1Gt rounding down', () => {
    const actual = formatCo2({ value: 994_320_320_231_123 });
    const expected = '994 Mt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles values up to 1 trillion grams, rounding up', () => {
    const actual = formatCo2({ value: 999_900_000_000_000 });
    const expected = '1000 Mt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles values above 1 trillion', () => {
    const actual = formatCo2({ value: 6_700_000_000_000_000 });
    const expected = '6.7 Gt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles values petatonnes', () => {
    const actual = formatCo2({ value: 1.5e21 });
    const expected = '1500 Tt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles negative values g', () => {
    const actual = formatCo2({ value: -9 });
    const expected = '−9 g';
    expect(actual).to.eq(expected);
  });
  it('handles negative values kg', () => {
    const actual = formatCo2({ value: -9000 });
    const expected = '−9 kg';
    expect(actual).to.eq(expected);
  });
  it('handles negative values t', () => {
    const actual = formatCo2({ value: -9_000_000 });
    const expected = '−9 t';
    expect(actual).to.eq(expected);
  });
  it('handles negative values kt', () => {
    const actual = formatCo2({ value: -9_000_000_000 });
    const expected = '−9 kt';
    expect(actual).to.eq(expected);
  });
  it('handles negative values Mt', () => {
    const actual = formatCo2({ value: -99_000_000_000_000 });
    const expected = '−99 Mt';
    expect(actual).to.deep.eq(expected);
  });
  it('uses same unit as another value would - negative t', () => {
    const actual = formatCo2({ value: -23_000, total: -2_350_000 });
    const expected = '−0.023 t';
    expect(actual).to.deep.eq(expected);
  });
  it('uses same unit as another value would - negative kg', () => {
    const actual = formatCo2({ value: -23_000, total: -24_000 });
    const expected = '−23 kg';
    expect(actual).to.deep.eq(expected);
  });
  it('handles real data value - negative', () => {
    const actual = formatCo2({ value: -740_703_650 });
    const expected = '−741 t';
    expect(actual).to.deep.eq(expected);
  });
  it('handles values petatonnes - negative', () => {
    const actual = formatCo2({ value: -1.5e21 });
    const expected = '−1500 Tt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles megatonnes close to 1Gt rounding down - negative', () => {
    const actual = formatCo2({ value: -994_320_320_231_123 });
    const expected = '−994 Mt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles values up to 1 trillion grams, rounding up - negative', () => {
    const actual = formatCo2({ value: -999_900_000_000_000 });
    const expected = '−1000 Mt';
    expect(actual).to.deep.eq(expected);
  });
  it('handles negative values correct when value to match is positive', () => {
    const actual = formatCo2({ value: -1_400_000_000, total: 1_400_000_000 });
    const expected = '−1.4 kt';
    expect(actual).to.eq(expected);
  });
});

describe('getDateTimeFormatOptions', () => {
  it('handles hourly data', () => {
    const actual = getDateTimeFormatOptions(TimeRange.H24, 'UTC');
    const expected = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      timeZone: 'UTC',
      timeZoneName: 'short',
    };
    expect(actual).to.deep.eq(expected);
  });

  it('handles hourly data without timezone', () => {
    const actual = getDateTimeFormatOptions(TimeRange.H24);
    const expected = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      timeZone: undefined,
      timeZoneName: 'short',
    };
    expect(actual).to.deep.eq(expected);
  });

  it('handles daily data', () => {
    const actual = getDateTimeFormatOptions(TimeRange.D30);
    const expected = {
      dateStyle: 'long',
      timeZone: 'UTC',
    };
    expect(actual).to.deep.eq(expected);
  });
  it('handles monthly data', () => {
    const actual = getDateTimeFormatOptions(TimeRange.M12);
    const expected = {
      month: 'long',
      year: 'numeric',
      timeZone: 'UTC',
    };
    expect(actual).to.deep.eq(expected);
  });
  it('handles yearly data', () => {
    const actual = getDateTimeFormatOptions(TimeRange.ALL);
    const expected = {
      year: 'numeric',
      timeZone: 'UTC',
    };
    expect(actual).to.deep.eq(expected);
  });
  it('logs an error on unknown data', () => {
    // Spy on console.error to check if it is called
    const consoleErrorSpy = vi.spyOn(console, 'error');

    const actual = getDateTimeFormatOptions('ThisAggregateDoesNotExist' as TimeRange);
    const expected = {};
    expect(actual).to.deep.eq(expected);
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'ThisAggregateDoesNotExist is not implemented'
    );

    // Restore the spy
    consoleErrorSpy.mockRestore();
  });
});

// These tests rely on the internal implementation of the `Intl.DateTimeFormat` object
// and may fail if the Node version changes. Simply update the snapshot if that is the case.
describe('formatDate', () => {
  it('handles invalid date', () => {
    const actual = formatDate(new Date('invalid-date'), 'en', TimeRange.H24);
    const expected = '';
    expect(actual).to.deep.eq(expected);
  });

  it('handles a date that is not a Date object', () => {
    const actual = formatDate('not-a-date' as unknown as Date, 'en', TimeRange.H24);
    const expected = '';
    expect(actual).to.deep.eq(expected);
  });

  it.each(['en', 'sv', 'de', 'fr', 'es', 'it'])(
    'handles hourly data for %s',
    (language) => {
      const actual = formatDate(
        new Date('2021-01-01T00:00:00Z'),
        language,
        TimeRange.H24
      );
      expect(actual).toMatchSnapshot();
    }
  );

  it.each(['en', 'sv', 'de', 'fr', 'es', 'it'])(
    'handles daily data for %s',
    (language) => {
      const actual = formatDate(
        new Date('2021-01-01T00:00:00Z'),
        language,
        TimeRange.D30
      );
      expect(actual).toMatchSnapshot();
    }
  );

  it.each(['en', 'sv', 'de', 'fr', 'es', 'it'])(
    'handles monthly data for %s',
    (language) => {
      const actual = formatDate(
        new Date('2021-01-01T00:00:00Z'),
        language,
        TimeRange.M12
      );
      expect(actual).toMatchSnapshot();
    }
  );

  it.each(['en', 'sv', 'de', 'fr', 'es', 'it'])(
    'handles yearly data for %s',
    (language) => {
      const actual = formatDate(
        new Date('2021-01-01T00:00:00Z'),
        language,
        TimeRange.ALL
      );
      expect(actual).toMatchSnapshot();
    }
  );

  it('logs an error on unknown data', () => {
    // Spy on console.error to check if it is called
    const consoleErrorSpy = vi.spyOn(console, 'error');

    const actual = formatDate(
      new Date('2021-01-01T00:00:00Z'),
      'en',
      'ThisAggregateDoesNotExist' as TimeRange
    );
    const expected = '1/1/2021';
    expect(actual).to.deep.eq(expected);
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'ThisAggregateDoesNotExist is not implemented'
    );

    // Restore the spy
    consoleErrorSpy.mockRestore();
  });
});

describe('scalePower', () => {
  it('should return default unit and formattingFactor when maxPower is undefined', () => {
    const result = scalePower(undefined);
    expect(result).toEqual({
      unit: '?',
      formattingFactor: 1e3,
    });
  });

  it('should return correct unit and formattingFactor for power values', () => {
    const result = scalePower(1e6, true);
    expect(result).toEqual({
      unit: PowerUnits.TERAWATTS,
      formattingFactor: 1e6,
    });
  });

  it('should return correct unit and formattingFactor for energy values', () => {
    const result = scalePower(1e6, false);
    expect(result).toEqual({
      unit: EnergyUnits.TERAWATT_HOURS,
      formattingFactor: 1e6,
    });
  });

  it('should handle negative maxPower values correctly', () => {
    const result = scalePower(-1e6, true);
    expect(result).toEqual({
      unit: PowerUnits.TERAWATTS,
      formattingFactor: 1e6,
    });
  });

  it('should return fallback unit and formattingFactor when no thresholds are met', () => {
    const result = scalePower(1e-10, false);
    expect(result).toEqual({
      unit: EnergyUnits.PETAWATT_HOURS,
      formattingFactor: 1e9,
    });
  });
});

describe('formatDateTick', () => {
  it('should return an empty string for invalid date', () => {
    const result = formatDateTick(new Date('invalid-date'), 'en', TimeRange.H24);
    expect(result).toBe('');
  });

  it('should format date correctly for HOURLY time aggregate', () => {
    const date = new Date('2023-01-01T12:00:00Z');
    const result = formatDateTick(date, 'en', TimeRange.H24);
    expect(result).toBe(
      new Intl.DateTimeFormat('en', { timeStyle: 'short' }).format(date)
    );
  });

  it('should format date correctly for DAILY time aggregate', () => {
    const date = new Date('2023-01-01T12:00:00Z');
    const result = formatDateTick(date, 'en', TimeRange.D30);
    expect(result).toBe(
      new Intl.DateTimeFormat('en', {
        month: 'short',
        day: 'numeric',
        timeZone: 'UTC',
      }).format(date)
    );
  });

  it('should format date correctly for MONTHLY time aggregate with language "et"', () => {
    const date = new Date('2023-01-01T12:00:00Z');
    const result = formatDateTick(date, 'et', TimeRange.M12);
    const expected = new Intl.DateTimeFormat('et', {
      month: 'short',
      day: 'numeric',
      timeZone: 'UTC',
    })
      .formatToParts(date)
      .find((part) => part.type === 'month')?.value;
    expect(result).toBe(expected);
  });

  it('should format date correctly for MONTHLY time aggregate with language not "et"', () => {
    const date = new Date('2023-01-01T12:00:00Z');
    const result = formatDateTick(date, 'en', TimeRange.M12);
    expect(result).toBe(
      new Intl.DateTimeFormat('en', { month: 'short', timeZone: 'UTC' }).format(date)
    );
  });

  it('should format date correctly for YEARLY time aggregate', () => {
    const date = new Date('2023-01-01T12:00:00Z');
    const result = formatDateTick(date, 'en', TimeRange.ALL);
    expect(result).toBe(
      new Intl.DateTimeFormat('en', { year: 'numeric', timeZone: 'UTC' }).format(date)
    );
  });

  it('should return an empty string for unimplemented time aggregate', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const result = formatDateTick(
      new Date('2023-01-01T12:00:00Z'),
      'en',
      'UNIMPLEMENTED' as TimeRange
    );
    expect(result).toBe('');
    expect(consoleSpy).toHaveBeenCalledWith('UNIMPLEMENTED is not implemented');
    consoleSpy.mockRestore();
  });
});

describe('formatDataSources', () => {
  it('should join data sources with a comma when Intl.ListFormat is undefined', () => {
    const originalListFormat = Intl.ListFormat;
    (Intl as any).ListFormat = undefined; // Temporarily set Intl.ListFormat to undefined

    const dataSources = ['source1', 'source2', 'source3'];
    const result = formatDataSources(dataSources, 'en');
    expect(result).toBe('source1, source2, source3');

    (Intl as any).ListFormat = originalListFormat; // Restore Intl.ListFormat
  });

  it('should format data sources correctly using Intl.ListFormat', () => {
    const dataSources = ['source1', 'source2', 'source3'];
    const result = formatDataSources(dataSources, 'en');
    expect(result).toBe(
      new Intl.ListFormat('en', { style: 'long', type: 'conjunction' }).format(
        dataSources
      )
    );
  });
});
