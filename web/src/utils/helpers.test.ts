import { getFossilFuelPercentage } from './helpers';

describe('getFossilFuelPercentage', () => {
  // Tests for consumption
  describe('consumption', () => {
    it('returns 1 when fossil fuel ratio is 0', () => {
      const actual = getFossilFuelPercentage(true, 0, 0);
      expect(actual).toBe(1);
    });

    it('returns 0 when fossil fuel ratio is 1', () => {
      const actual = getFossilFuelPercentage(true, 1, 1);
      expect(actual).toBe(0);
    });

    it('returns NaN when fossil fuel ratio is null', () => {
      const actual = getFossilFuelPercentage(true, null, null);
      expect(actual).toBeNaN();
    });

    it('returns NaN when fossil fuel ratio is undefined', () => {
      const actual = getFossilFuelPercentage(true, undefined, undefined);
      expect(actual).toBeNaN();
    });

    it('returns 1 - fossil fuel ratio when fossil fuel ratio is between 0 and 1', () => {
      const actual = getFossilFuelPercentage(true, 0.3, 0.5);
      expect(actual).toBe(0.7);
    });
  });

  // Tests for production
  describe('production', () => {
    it('returns 1 when fossil fuel ratio is 0', () => {
      const actual = getFossilFuelPercentage(false, 0, 0);
      expect(actual).toBe(1);
    });

    it('returns 0 when fossil fuel ratio is 1', () => {
      const actual = getFossilFuelPercentage(false, 1, 1);
      expect(actual).toBe(0);
    });

    it('returns NaN when fossil fuel ratio is null', () => {
      const actual = getFossilFuelPercentage(false, null, null);
      expect(actual).toBeNaN();
    });

    it('returns NaN when fossil fuel ratio is undefined', () => {
      const actual = getFossilFuelPercentage(false, undefined, undefined);
      expect(actual).toBeNaN();
    });

    it('returns 1 - fossil fuel ratio when fossil fuel ratio is between 0 and 1', () => {
      const actual = getFossilFuelPercentage(false, 0.5, 0.3);
      expect(actual).toBe(0.7);
    });
  });
});
