const co2eq_parameters = require('./co2eq_parameters.json');
const { STORAGE_MODES, PRODUCTION_MODES } = require('../web/src/helpers/constants.js');
const ALL_MODES = [
  // Note the `discharge` and `charge` keys are used by the marginal
  // TODO: Define somewhere in a language agnostic manner
  // all emission factor keys (including discharge/charge)
  ...STORAGE_MODES.map(k => [`${k} discharge`, `${k} charge`]).flat(),
  ...PRODUCTION_MODES,
];

describe('Each fallbackZoneMixes sums to one', () => {
  it.each([
    ['defaults', co2eq_parameters.fallbackZoneMixes.defaults],
    ...Object.entries(co2eq_parameters.fallbackZoneMixes.zoneOverrides),
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

describe('verify keys in emission factors are valid', () => {
  it.each([
    ['defaults', co2eq_parameters.emissionFactors.defaults],
    ...Object.entries(co2eq_parameters.emissionFactors.zoneOverrides),
  ])('for zone %s', (zone, value) => {
    Object.keys(value).forEach(key => expect(ALL_MODES).toContain(key));
  });
});

describe('verify keys in fallbackZoneMixes factors are valid', () => {
  it.each([
    ['defaults', co2eq_parameters.fallbackZoneMixes.defaults],
    ...Object.entries(co2eq_parameters.fallbackZoneMixes.zoneOverrides),
  ])('for zone %s', (zone, value) => {
    Object.keys(value.powerOriginRatios).forEach(key => expect(ALL_MODES).toContain(key));
  });
});
