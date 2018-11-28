var exports = module.exports = {};

const co2eqParameters = require('./co2eq_parameters.json');

exports.footprintOf = function(mode, zoneKey) {
  const fallbackCarbonIntensity = (co2eqParameters.fallbackZoneMixes[zoneKey] || {}).carbonIntensity;
  if (mode === 'hydro discharge' && fallbackCarbonIntensity) {
    return fallbackCarbonIntensity;
  }
  const defaultFootprint = co2eqParameters.emissionFactors.defaults[mode];
  const override = (co2eqParameters.emissionFactors.zoneOverrides[zoneKey] || {})[mode];
  return (override || defaultFootprint || {}).value;
};
exports.sourceOf = function(mode, zoneKey) {
  const defaultFootprint = co2eqParameters.emissionFactors.defaults[mode];
  const override = (co2eqParameters.emissionFactors.zoneOverrides[zoneKey] || {})[mode];
  return (override || defaultFootprint || {}).source;
};
exports.defaultExportIntensityOf = zoneKey =>
  (co2eqParameters.fallbackZoneMixes[zoneKey] || {}).carbonIntensity;
exports.defaultRenewableRatioOf = zoneKey =>
  (co2eqParameters.fallbackZoneMixes[zoneKey] || {}).renewableRatio;
exports.defaultFossilFuelRatioOf = zoneKey =>
  (co2eqParameters.fallbackZoneMixes[zoneKey] || {}).fossilFuelRatio;
