const co2eq_parameters_lifecycle = require("./co2eq_parameters_lifecycle.json");
const co2eq_parameters_all = require("./co2eq_parameters_all.json");
const co2eq_parameters = {
  ...co2eq_parameters_all,
  ...co2eq_parameters_lifecycle,
};
const {
  STORAGE_MODES,
  PRODUCTION_MODES,
} = require("../web/src/helpers/constants.js");
const ALL_MODES = [
  // Note the `discharge` and `charge` keys are used by the marginal
  // TODO: Define somewhere in a language agnostic manner
  // all emission factor keys (including discharge/charge)
  ...STORAGE_MODES.map((k) => [`${k} discharge`, `${k} charge`]).flat(),
  ...PRODUCTION_MODES,
];

describe("Each fallbackZoneMixes sums to one", () => {
  it.each([
    ["defaults", co2eq_parameters.fallbackZoneMixes.defaults],
    ...Object.entries(co2eq_parameters.fallbackZoneMixes.zoneOverrides),
  ])("for zone %s", (zone, fallbackZoneMix) => {
    // Verify the key exists
    expect(fallbackZoneMix.powerOriginRatios).toBeTruthy();

    if (fallbackZoneMix.powerOriginRatios) {
      if (Array.isArray(fallbackZoneMix.powerOriginRatios)) {
        // Case where powerOriginRatios is an array of yearly objects for the ratios
        Object.values(
          fallbackZoneMix.powerOriginRatios
        ).forEach((yearlyRatios) => {
          const total = Object.values(yearlyRatios).filter(Number).reduce((acc, cur) => acc + cur, 0);
          expect(total).toBeCloseTo(1);
        });
      } else if (fallbackZoneMix.powerOriginRatios) {
        // Default case where powerOriginRatios is an object of the ratios
        const total = Object.values(fallbackZoneMix.powerOriginRatios).filter(Number).reduce((acc, cur) => acc + cur, 0);
        expect(total).toBeCloseTo(1);
      };
    };
  });
});

describe("verify keys in emission factors are valid", () => {
  it.each([
    ["defaults", co2eq_parameters.emissionFactors.defaults],
    ...Object.entries(co2eq_parameters.emissionFactors.zoneOverrides),
  ])("for zone %s", (zone, value) => {
    Object.keys(value).forEach((key) => expect(ALL_MODES).toContain(key));
  });
});

describe("verify keys in fallbackZoneMixes factors are valid", () => {
  it.each([
    ["defaults", co2eq_parameters.fallbackZoneMixes.defaults],
    ...Object.entries(co2eq_parameters.fallbackZoneMixes.zoneOverrides),
  ])("for zone %s", (zone, value) => {
    if (Array.isArray(value.powerOriginRatios)) {
      // Case where powerOriginRatios is an array of yearly objects for the ratios
      const NON_RATIO_KEYS = ["_source", "_comment", "datetime"];
      Object.values(value.powerOriginRatios).forEach((yearlyRatios) => {
        Object.keys(yearlyRatios).filter(key => !NON_RATIO_KEYS.includes(key)).forEach((key) => expect(ALL_MODES).toContain(key));
      });
    } else if (value.powerOriginRatios) {
      // Default case where powerOriginRatios is an object of the ratios
      Object.keys(value.powerOriginRatios).forEach((key) =>
        expect(ALL_MODES).toContain(key)
      );
    };
  });
});
