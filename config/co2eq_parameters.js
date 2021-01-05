var exports = module.exports = {};

const co2eqParameters = require('./co2eq_parameters.json');

exports.footprintOf = function(mode, zoneKey) {
  const defaultFootprint = co2eqParameters.emissionFactors.defaults[mode];
  const override = (co2eqParameters.emissionFactors.zoneOverrides[zoneKey] || {})[mode];
  const value = (override || defaultFootprint).value;
  if (value == null) {
    throw new Error(`Couldn't find footprint of ${mode} for ${zoneKey}`);
  }
  return value;
};
exports.sourceOf = function(mode, zoneKey) {
  const defaultFootprint = co2eqParameters.emissionFactors.defaults[mode];
  const override = (co2eqParameters.emissionFactors.zoneOverrides[zoneKey] || {})[mode];
  return (override || defaultFootprint || {}).source;
};

exports.defaultExportIntensityOf = zoneKey => {
  const mix = (co2eqParameters.fallbackZoneMixes.zoneOverrides[zoneKey] ||
    co2eqParameters.fallbackZoneMixes.defaults).powerOriginRatios;
  // Compute footprint
  // Note that all mix values sum to 1 so we can simply do a scalar product
  return Object.entries(mix)
    .map(([mode, v]) => v * exports.footprintOf(mode, zoneKey))
    .reduce((a, b) => a + b, 0);
}

exports.defaultRenewableRatioOf = (zoneKey) => {
    // if `zoneKey` has ratios in co2eqparameters, then use those ratios
  const ratios = (co2eqParameters.fallbackZoneMixes.zoneOverrides[zoneKey] ||
    co2eqParameters.fallbackZoneMixes.defaults).powerOriginRatios;

  return Object.keys(ratios)
    // only keep the keys that are renewable
    .filter(fuelKey => exports.renewableAccessor(zoneKey, fuelKey, 1) === 1)
    // obtain the values
    .map(fuelKey => ratios[fuelKey])
    // take the sum
    .reduce((a, b) => a + b, 0)
}

exports.defaultFossilFuelRatioOf = (zoneKey) => {
  // if zonekey has ratios in co2eqparameters, then those ratios
  const ratios = (co2eqParameters.fallbackZoneMixes.zoneOverrides[zoneKey] ||
    co2eqParameters.fallbackZoneMixes.defaults).powerOriginRatios;

  return Object.keys(ratios)
    // only keep the keys that are renewable
    .filter(fuelKey => exports.fossilFuelAccessor(zoneKey, fuelKey, 1) === 1)
    // obtain the values
    .map(fuelKey => ratios[fuelKey])
    // take the sum
    .reduce((a, b) => a + b, 0)
}

exports.fossilFuelAccessor = (zoneKey, k, v) => {
  return (k == 'coal' ||
          k == 'gas' ||
          k == 'oil' ||
          (k === 'unknown' && (zoneKey !== 'GB-ORK' && zoneKey !== 'UA' && zoneKey !== 'SG' && zoneKey !== 'PR' && zoneKey !== 'FO')) ||
          k == 'other') ? 1 : 0;
}

exports.renewableAccessor = (zoneKey, k, v) => {
  return (exports.fossilFuelAccessor(zoneKey, k, v) ||
          k === 'nuclear') ? 0 : 1;
  // TODO(bl): remove storage from renewable list?
}

exports.defaultPowerOriginRatio = (zoneKey, fuelKey) => {
  // if no ratios found for that zoneKey, use defaults
  return (co2eqParameters.fallbackZoneMixes.zoneOverrides[zoneKey] ||
                 co2eqParameters.fallbackZoneMixes.defaults)
                    .powerOriginRatios[fuelKey];
}

exports.defaultPowerOriginRatioFuel = (fuelKey) => {
  return function powerOriginRatioWithFuelSet(zoneKey) {
    return exports.defaultPowerOriginRatio(zoneKey, fuelKey)
  }
}
