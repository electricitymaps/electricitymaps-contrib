const defaultCO2Params = require('./co2eq_parameters.json');

describe('Each fallbackZoneMixes sums to one', () => {
  it.each([
    ['defaults', defaultCO2Params.fallbackZoneMixes.defaults],
    ...Object.entries(defaultCO2Params.fallbackZoneMixes.zoneOverrides),
  ])('for zone %s', (zone, fallbackZoneMix) => {
    // Verify the key exists
    expect(fallbackZoneMix.powerOriginRatios).toBeTruthy();
    if (fallbackZoneMix.powerOriginRatios) {
      const totalRatio = Object.values(fallbackZoneMix.powerOriginRatios).reduce(
        (a, b) => a + b,
        0
      );
      expect(totalRatio).toBeCloseTo(1);
    }
  });
});
