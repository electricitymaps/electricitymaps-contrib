export function getElectricityProductionValue({
  capacity,
  isStorage,
  production,
  storage,
}) {
  const value = isStorage ? -storage : production;
  // If the value is not defined but the capacity
  // is zero, assume the value is also zero.
  if (!Number.isFinite(value) && capacity === 0) {
    return 0;
  }
  return value;
}

export function getProductionCo2Intensity(mode, zoneData) {
  const isStorage = mode.indexOf('storage') !== -1;
  const resource = mode.replace(' storage', '');

  const storage = (zoneData.storage || {})[resource];
  const storageCo2Intensity = (zoneData.storageCo2Intensities || {})[resource];
  const dischargeCo2Intensity = (zoneData.dischargeCo2Intensities || {})[resource];
  const productionCo2Intensity = (zoneData.productionCo2Intensities || {})[resource];

  return isStorage
    ? (
      storage > 0
        ? storageCo2Intensity
        : dischargeCo2Intensity
    ) : (
      productionCo2Intensity
    );
}

export function getExchangeCo2Intensity(mode, zoneData, electricityMixMode) {
  const exchange = (zoneData.exchange || {})[mode];
  const exchangeCo2Intensity = (zoneData.exchangeCo2Intensities || {})[mode];

  return exchange >= 0
    ? (
      exchangeCo2Intensity
    ) : (
      electricityMixMode === 'consumption'
        ? zoneData.co2intensity
        : zoneData.co2intensityProduction
    );
}

export function getTotalElectricity(zoneData, displayByEmissions) {
  const productionValue = displayByEmissions
    ? zoneData.totalCo2Production
    : zoneData.totalProduction;

  if (productionValue == null) {
    return NaN;
  }

  return displayByEmissions
    ? (productionValue + zoneData.totalCo2Discharge + zoneData.totalCo2Import) // gCO₂eq/h
    : (productionValue + zoneData.totalDischarge + zoneData.totalImport);
}
