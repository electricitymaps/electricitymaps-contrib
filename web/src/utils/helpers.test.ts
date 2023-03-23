import { getFossilFuelRatio, getCarbonIntensity, getRenewableRatio } from './helpers';

describe('getFossilFuelPercentage', () => {
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
