import { ElectricityStorageType, ZoneDetail } from 'types';
import { describe, expect, it } from 'vitest';

import {
  extractLinkFromSource,
  getElectricityProductionValue,
  getGenerationTypeKey,
  getNextDatetime,
  getRatioPercent,
  getStorageKey,
  getTimeScale,
  getTooltipPosition,
  getTotalElectricityAvailable,
  getTotalEmissionsAvailable,
} from './graphUtils';

describe('getTimeScale', () => {
  it('should return null if startTime is not provided', () => {
    const result = getTimeScale(500, null, new Date());
    expect(result).toBeNull();
  });

  it('should return null if endTime is not provided', () => {
    const result = getTimeScale(500, new Date(), null);
    expect(result).toBeNull();
  });

  it('should return a scaleTime function when both startTime and endTime are provided', () => {
    const startTime = new Date('2023-01-01T00:00:00Z');
    const endTime = new Date('2023-01-02T00:00:00Z');
    const result = getTimeScale(500, startTime, endTime);
    if (result) {
      expect(result.domain()).toEqual([startTime, endTime]);
      expect(result.range()).toEqual([0, 500]);
    } else {
      throw new Error('Expected result to be a scaleTime function');
    }
  });

  it('should correctly set the domain and range of the scale', () => {
    const startTime = new Date('2023-01-01T00:00:00Z');
    const endTime = new Date('2023-01-02T00:00:00Z');
    const width = 800;
    const result = getTimeScale(width, startTime, endTime);
    if (result) {
      expect(result.domain()).toEqual([startTime, endTime]);
      expect(result.range()).toEqual([0, width]);
    } else {
      throw new Error('Expected result to be a scaleTime function');
    }
  });
});

describe('getTooltipPosition', () => {
  it('should return { x: 0, y: 0 } when isMobile is true', () => {
    const isMobile = true;
    const marker = { x: 100, y: 200 };
    const result = getTooltipPosition(isMobile, marker);
    expect(result).toEqual({ x: 0, y: 0 });
  });

  it('should return the marker position when isMobile is false', () => {
    const isMobile = false;
    const marker = { x: 100, y: 200 };
    const result = getTooltipPosition(isMobile, marker);
    expect(result).toEqual(marker);
  });
});

describe('getStorageKey', () => {
  it('should return the storage key for hydro storage', () => {
    const result = getStorageKey('hydro storage');
    expect(result).toEqual('hydro');
  });

  it('should return the storage key for battery storage', () => {
    const result = getStorageKey('battery storage');
    expect(result).toEqual('battery');
  });

  it('should return undefined for other storage types', () => {
    const result = getStorageKey('other storage' as ElectricityStorageType);
    expect(result).toBeUndefined();
  });
});

describe('getRatioPercent', () => {
  it.each([
    [0, 0, 0],
    [10, 0, '?'],
    [0, 10, 0],
    [5, 5, 100],
    [1, 5, 20],
    [Number.NaN, 5, '?'],
    [5, Number.NaN, '?'],
    [Number.NaN, Number.NaN, '?'],
    [null, 5, '?'],
    [5, null, '?'],
  ])('handles %s of %s', (a, b, expected) => {
    const actual = getRatioPercent(a, b);
    expect(actual).toEqual(expected);
  });
});

describe('getGenerationTypeKey', () => {
  it('should return the generation type key if it exists in modeOrder', () => {
    const name = 'solar';
    const result = getGenerationTypeKey(name);
    expect(result).toEqual(name);
  });

  it('should return undefined if the generation type key does not exist in modeOrder', () => {
    const name = 'undefined';
    const result = getGenerationTypeKey(name);
    expect(result).toBeUndefined();
  });
});

describe('getNextDatetime', () => {
  it('should return the next datetime if currentDate exists in the array', () => {
    const datetimes = [
      new Date('2023-01-01T00:00:00Z'),
      new Date('2023-01-02T00:00:00Z'),
      new Date('2023-01-03T00:00:00Z'),
    ];
    const currentDate = new Date('2023-01-02T00:00:00Z');
    const result = getNextDatetime(datetimes, currentDate);
    expect(result).toEqual(new Date('2023-01-03T00:00:00Z'));
  });

  it('should return undefined if currentDate is the last element in the array', () => {
    const datetimes = [
      new Date('2023-01-01T00:00:00Z'),
      new Date('2023-01-02T00:00:00Z'),
      new Date('2023-01-03T00:00:00Z'),
    ];
    const currentDate = new Date('2023-01-03T00:00:00Z');
    const result = getNextDatetime(datetimes, currentDate);
    expect(result).toBeUndefined();
  });

  it('should return undefined if currentDate does not exist in the array', () => {
    const datetimes = [
      new Date('2023-01-01T00:00:00Z'),
      new Date('2023-01-02T00:00:00Z'),
      new Date('2023-01-03T00:00:00Z'),
    ];
    const currentDate = new Date('2023-01-04T00:00:00Z');
    const result = getNextDatetime(datetimes, currentDate);
    expect(result).toBeUndefined();
  });
});

describe('getElectricityProductionValue', () => {
  it('handles production', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 61_370,
      isStorage: false,
      generationTypeStorage: undefined,
      generationTypeProduction: 41_161,
    });
    expect(actual).toEqual(41_161);
  });

  it('handles storage', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 20_222.25,
      isStorage: true,
      generationTypeStorage: -3738.75,
      generationTypeProduction: 11_930.25,
    });
    expect(actual).toEqual(3738.75);
  });

  it('handles missing storage', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 123,
      isStorage: true,
      generationTypeStorage: null,
      generationTypeProduction: 999,
    });
    expect(actual).toEqual(null);
  });

  it('handles zero storage', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 123,
      isStorage: true,
      generationTypeStorage: 0,
      generationTypeProduction: 999,
    });
    expect(actual).toEqual(0);
  });

  it('handles zero production', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 123,
      isStorage: false,
      generationTypeStorage: undefined,
      generationTypeProduction: 0,
    });
    expect(actual).toEqual(0);
  });

  it('handles null production', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 16,
      isStorage: false,
      generationTypeStorage: undefined,
      generationTypeProduction: null,
    });
    expect(actual).toEqual(null);
  });

  it('handles zero capacity', () => {
    const actual = getElectricityProductionValue({
      generationTypeCapacity: 0,
      isStorage: false,
      generationTypeStorage: undefined,
      generationTypeProduction: 0,
    });
    expect(actual).toEqual(0);
  });
});

describe('getTotalEmissionsAvailable and ElectricityAvailable', () => {
  const zoneData = {
    totalCo2Production: 100,
    totalCo2Consumption: 5,
    totalConsumption: 50,
    totalCo2Discharge: 50,
    totalProduction: 200,
    totalDischarge: 50,
    totalImport: 100,
    totalCo2Import: 25,
  } as ZoneDetail;

  it('handles emissions for consumption', () => {
    const actual = getTotalEmissionsAvailable(zoneData, true);
    expect(actual).toEqual(175);
  });

  it('handles power for consumption', () => {
    const actual = getTotalElectricityAvailable(zoneData, true);
    expect(actual).toEqual(350);
  });

  it('handles emissions for production', () => {
    const actual = getTotalEmissionsAvailable(zoneData, false);
    expect(actual).toEqual(150);
  });

  it('returns NaN when missing productionValue', () => {
    const actual = getTotalEmissionsAvailable(
      { ...zoneData, totalCo2Production: null } as unknown as ZoneDetail,
      false
    );
    expect(actual).toEqual(Number.NaN);
  });

  it('handles power for production', () => {
    const actual = getTotalElectricityAvailable(zoneData, false);
    expect(actual).toEqual(250);
  });

  it('returns 0 when productionValue is 0', () => {
    const actual = getTotalElectricityAvailable(
      { ...zoneData, totalProduction: 0, totalDischarge: 0 },
      false
    );
    expect(actual).toEqual(0);
  });

  it('returns NaN when missing productionValue', () => {
    const actual = getTotalElectricityAvailable(
      { ...zoneData, totalProduction: null },
      false
    );
    expect(actual).toEqual(Number.NaN);
  });
});

describe('extractLinkFromSource', () => {
  const sourceLinkMapping = {
    source1: 'http://mappedlink1.com',
    source2: 'http://mappedlink2.com',
    Climatescope: 'https://www.global-climatescope.org/',
  };

  it('should return mapped link if source is in sourceLinkMapping', () => {
    expect(extractLinkFromSource('source1', sourceLinkMapping)).toEqual(
      'http://mappedlink1.com'
    );
    expect(extractLinkFromSource('source2', sourceLinkMapping)).toEqual(
      'http://mappedlink2.com'
    );
  });

  it('should work with a real link', () => {
    expect(extractLinkFromSource('Climatescope', sourceLinkMapping)).toEqual(
      'https://www.global-climatescope.org/'
    );
  });

  it('should return null if source does not include a dot', () => {
    expect(extractLinkFromSource('sourceWithoutDot', sourceLinkMapping)).toBeNull();
  });

  it('should return source if source includes http', () => {
    expect(
      extractLinkFromSource('http://sourceWithHttp.com', sourceLinkMapping)
    ).to.equal('http://sourceWithHttp.com');
  });

  it('should return source with http prefix if source includes a dot but not http', () => {
    expect(extractLinkFromSource('sourceWithDot.com', sourceLinkMapping)).toEqual(
      'http://sourceWithDot.com'
    );
  });
});
