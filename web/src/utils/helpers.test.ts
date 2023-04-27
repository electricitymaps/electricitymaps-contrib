import {
  getCO2IntensityByMode,
  dateToDatetimeString,
  getProductionCo2Intensity,
  getFossilFuelRatio,
  getCarbonIntensity,
  getRenewableRatio,
} from './helpers';

import { zoneDetailMock } from 'stories/mockData';

describe('getCO2IntensityByMode', () => {
  // Tests for consumption
  describe('consumption', () => {
    it('returns 100 when the mode is consumption', () => {
      const actual = getCO2IntensityByMode(
        { co2intensity: 100, co2intensityProduction: 200 },
        'consumption'
      );
      expect(actual).toBe(100);
    });
  });

  // Tests for production
  describe('production', () => {
    it('returns 200 when the mode is production', () => {
      const actual = getCO2IntensityByMode(
        { co2intensity: 100, co2intensityProduction: 200 },
        'production'
      );
      expect(actual).toBe(200);
    });
  });
});

describe('dateToDatetimeString', () => {
  it('returns the correct datetime string', () => {
    const actual = dateToDatetimeString(new Date('2023-01-01T12:00:00Z'));
    expect(actual).toBe('2023-01-01T12:00:00Z');
  });
});

describe('getProductionCo2Intensity', () => {
  it('returns the correct value when the type is hydro', () => {
    const actual = getProductionCo2Intensity('hydro', zoneDetailMock);
    expect(actual).toBe(10.7);
  });

  it('returns the correct value when the type is battery storage', () => {
    const actual = getProductionCo2Intensity('battery storage', zoneDetailMock);
    expect(actual).toBe(136.442_667_362_438_53);
  });
});

describe('getFossilFuelRatio', () => {
  // Tests for consumption
  describe('consumption', () => {
    it('returns 1 when fossil fuel ratio is 0', () => {
      const actual = getFossilFuelRatio(true, 0, 0);
      expect(actual).toBe(1);
    });

    it('returns 0 when fossil fuel ratio is 1', () => {
      const actual = getFossilFuelRatio(true, 1, 1);
      expect(actual).toBe(0);
    });

    it('returns NaN when fossil fuel ratio is null', () => {
      const actual = getFossilFuelRatio(true, null, null);
      expect(actual).toBeNaN();
    });

    it('returns NaN when fossil fuel ratio is undefined', () => {
      const actual = getFossilFuelRatio(true, undefined, undefined);
      expect(actual).toBeNaN();
    });

    it('returns 1 - fossil fuel ratio when fossil fuel ratio is between 0 and 1', () => {
      const actual = getFossilFuelRatio(true, 0.3, 0.5);
      expect(actual).toBe(0.7);
    });
  });

  // Tests for production
  describe('production', () => {
    it('returns 1 when fossil fuel ratio is 0', () => {
      const actual = getFossilFuelRatio(false, 0, 0);
      expect(actual).toBe(1);
    });

    it('returns 0 when fossil fuel ratio is 1', () => {
      const actual = getFossilFuelRatio(false, 1, 1);
      expect(actual).toBe(0);
    });

    it('returns NaN when fossil fuel ratio is null', () => {
      const actual = getFossilFuelRatio(false, null, null);
      expect(actual).toBeNaN();
    });

    it('returns NaN when fossil fuel ratio is undefined', () => {
      const actual = getFossilFuelRatio(false, undefined, undefined);
      expect(actual).toBeNaN();
    });

    it('returns 1 - fossil fuel ratio when fossil fuel ratio is between 0 and 1', () => {
      const actual = getFossilFuelRatio(false, 0.5, 0.3);
      expect(actual).toBe(0.7);
    });
  });
});

describe('getCarbonIntensity', () => {
  // Tests for consumption
  describe('consumption', () => {
    it('returns carbon intensity when carbon intensity is not null', () => {
      const actual = getCarbonIntensity(true, 100, 200);
      expect(actual).toBe(100);
    });

    it('returns NaN when carbon intensity is null', () => {
      const actual = getCarbonIntensity(true, null, null);
      expect(actual).toBeNaN();
    });

    it('returns NaN when carbon intensity is undefined', () => {
      const actual = getCarbonIntensity(true, undefined, undefined);
      expect(actual).toBeNaN();
    });
  });

  // Tests for production
  describe('production', () => {
    it('returns carbon intensity when carbon intensity is not null', () => {
      const actual = getCarbonIntensity(false, 100, 200);
      expect(actual).toBe(200);
    });

    it('returns NaN when carbon intensity is null', () => {
      const actual = getCarbonIntensity(false, null, null);
      expect(actual).toBeNaN();
    });

    it('returns NaN when carbon intensity is undefined', () => {
      const actual = getCarbonIntensity(false, undefined, undefined);
      expect(actual).toBeNaN();
    });
  });
});

describe('getRenewableRatio', () => {
  // Tests for consumption
  describe('consumption', () => {
    it('returns renewable ratio when renewable ratio is not null', () => {
      const actual = getRenewableRatio(true, 0.5, 0.3);
      expect(actual).toBe(0.5);
    });

    it('returns NaN when renewable ratio is null', () => {
      const actual = getRenewableRatio(true, null, null);
      expect(actual).toBeNaN();
    });

    it('returns NaN when renewable ratio is undefined', () => {
      const actual = getRenewableRatio(true, undefined, undefined);
      expect(actual).toBeNaN();
    });
  });

  // Tests for production
  describe('production', () => {
    it('returns renewable ratio when renewable ratio is not null', () => {
      const actual = getRenewableRatio(false, 0.5, 0.3);
      expect(actual).toBe(0.3);
    });

    it('returns NaN when renewable ratio is null', () => {
      const actual = getRenewableRatio(false, null, null);
      expect(actual).toBeNaN();
    });

    it('returns NaN when renewable ratio is undefined', () => {
      const actual = getRenewableRatio(false, undefined, undefined);
      expect(actual).toBeNaN();
    });
  });
});
