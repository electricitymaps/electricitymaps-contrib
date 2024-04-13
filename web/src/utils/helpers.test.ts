import { zoneDetailMock } from 'stories/mockData';

import {
  dateToDatetimeString,
  getCarbonIntensity,
  getCO2IntensityByMode,
  getFossilFuelRatio,
  getProductionCo2Intensity,
  getRenewableRatio,
} from './helpers';

describe('getCO2IntensityByMode', () => {
  // Tests for consumption
  describe('consumption', () => {
    it('returns 100 when the mode is consumption', () => {
      const actual = getCO2IntensityByMode(
        { c: { ci: 100 }, p: { ci: 200 } },
        'consumption'
      );
      expect(actual).to.eq(100);
    });
  });

  // Tests for production
  describe('production', () => {
    it('returns 200 when the mode is production', () => {
      const actual = getCO2IntensityByMode(
        { c: { ci: 100 }, p: { ci: 200 } },
        'production'
      );
      expect(actual).to.eq(200);
    });
  });
});

describe('dateToDatetimeString', () => {
  it('returns the correct datetime string', () => {
    const actual = dateToDatetimeString(new Date('2023-01-01T12:00:00Z'));
    expect(actual).to.eq('2023-01-01T12:00:00Z');
  });
});

describe('getProductionCo2Intensity', () => {
  it('returns the correct value when the type is hydro', () => {
    const actual = getProductionCo2Intensity('hydro', zoneDetailMock);
    expect(actual).to.eq(10.7);
  });

  it('returns the correct value when the type is battery storage', () => {
    const actual = getProductionCo2Intensity('battery storage', zoneDetailMock);
    expect(actual).to.eq(155.11);
  });
});

describe('getFossilFuelRatio', () => {
  // Tests for consumption
  describe('consumption', () => {
    it('returns 1 when fossil fuel ratio is 0', () => {
      const actual = getFossilFuelRatio({ c: { fr: 0 }, p: { fr: 1 } }, true);
      expect(actual).to.eq(1);
    });

    it('returns 0 when fossil fuel ratio is 1', () => {
      const actual = getFossilFuelRatio({ c: { fr: 1 }, p: { fr: 0 } }, true);
      expect(actual).to.eq(0);
    });

    it('returns NaN when fossil fuel ratio is null', () => {
      const actual = getFossilFuelRatio({ c: { fr: null }, p: { fr: null } }, true);
      expect(actual).to.be.NaN;
    });

    it('returns NaN when fossil fuel ratio is undefined', () => {
      const actual = getFossilFuelRatio({ c: {}, p: {} }, true);
      expect(actual).to.be.NaN;
    });

    it('returns 1 - fossil fuel ratio when fossil fuel ratio is between 0 and 1', () => {
      const actual = getFossilFuelRatio({ c: { fr: 0.3 }, p: { fr: 0.7 } }, true);
      expect(actual).to.eq(0.7);
    });
  });

  // Tests for production
  describe('production', () => {
    it('returns 1 when fossil fuel ratio is 0', () => {
      const actual = getFossilFuelRatio({ c: { fr: 1 }, p: { fr: 0 } }, false);
      expect(actual).to.eq(1);
    });

    it('returns 0 when fossil fuel ratio is 1', () => {
      const actual = getFossilFuelRatio({ c: { fr: 0 }, p: { fr: 1 } }, false);
      expect(actual).to.eq(0);
    });

    it('returns NaN when fossil fuel ratio is null', () => {
      const actual = getFossilFuelRatio({ c: { fr: null }, p: { fr: null } }, false);
      expect(actual).to.be.NaN;
    });

    it('returns NaN when fossil fuel ratio is undefined', () => {
      const actual = getFossilFuelRatio({ c: {}, p: {} }, false);
      expect(actual).to.be.NaN;
    });

    it('returns 1 - fossil fuel ratio when fossil fuel ratio is between 0 and 1', () => {
      const actual = getFossilFuelRatio({ c: { fr: 0.7 }, p: { fr: 0.3 } }, false);
      expect(actual).to.eq(0.7);
    });
  });
});

describe('getCarbonIntensity', () => {
  // Tests for consumption
  describe('consumption', () => {
    it('returns carbon intensity when carbon intensity is not null', () => {
      const actual = getCarbonIntensity({ c: { ci: 100 }, p: { ci: 200 } }, true);
      expect(actual).to.eq(100);
    });

    it('returns NaN when carbon intensity is null', () => {
      const actual = getCarbonIntensity({ c: { fr: null }, p: { fr: null } }, true);
      expect(actual).to.be.NaN;
    });

    it('returns NaN when carbon intensity is undefined', () => {
      const actual = getCarbonIntensity({ c: {}, p: {} }, true);
      expect(actual).to.be.NaN;
    });
  });

  // Tests for production
  describe('production', () => {
    it('returns carbon intensity when carbon intensity is not null', () => {
      const actual = getCarbonIntensity({ c: { ci: 100 }, p: { ci: 200 } }, false);
      expect(actual).to.eq(200);
    });

    it('returns NaN when carbon intensity is null', () => {
      const actual = getCarbonIntensity({ c: { fr: null }, p: { fr: null } }, false);
      expect(actual).to.be.NaN;
    });

    it('returns NaN when carbon intensity is undefined', () => {
      const actual = getCarbonIntensity({ c: {}, p: {} }, false);
      expect(actual).to.be.NaN;
    });
  });
});

describe('getRenewableRatio', () => {
  // Tests for consumption
  describe('consumption', () => {
    it('returns renewable ratio when renewable ratio is not null', () => {
      const actual = getRenewableRatio({ c: { rr: 0.5 }, p: { rr: 0.3 } }, true);
      expect(actual).to.eq(0.5);
    });

    it('returns NaN when renewable ratio is null', () => {
      const actual = getRenewableRatio({ c: { rr: null }, p: { rr: null } }, true);
      expect(actual).to.be.NaN;
    });

    it('returns NaN when renewable ratio is undefined', () => {
      const actual = getRenewableRatio({ c: {}, p: {} }, true);
      expect(actual).to.be.NaN;
    });
  });

  // Tests for production
  describe('production', () => {
    it('returns renewable ratio when renewable ratio is not null', () => {
      const actual = getRenewableRatio({ c: { rr: 0.5 }, p: { rr: 0.3 } }, false);
      expect(actual).to.eq(0.3);
    });

    it('returns NaN when renewable ratio is null', () => {
      const actual = getRenewableRatio({ c: { rr: null }, p: { rr: null } }, false);
      expect(actual).to.be.NaN;
    });

    it('returns NaN when renewable ratio is undefined', () => {
      const actual = getRenewableRatio({ c: {}, p: {} }, false);
      expect(actual).to.be.NaN;
    });
  });
});
