import { ZoneDetail } from 'types';

export function getCO2IntensityByMode(
  zoneData: { co2intensity: number; co2intensityProduction: number },
  electricityMixMode: string
) {
  return electricityMixMode === 'consumption'
    ? zoneData.co2intensity
    : zoneData.co2intensityProduction;
}

/**
 * Converts date to format returned by API
 */
export function dateToDatetimeString(date: Date) {
  return date.toISOString().split('.')[0] + 'Z';
}

export function getProductionCo2Intensity(mode: string, zoneData: any) {
  const isStorage = mode.includes('storage');
  const resource = mode.replace(' storage', '');

  const storage = (zoneData.storage || {})[resource];
  const storageCo2Intensity = (zoneData.storageCo2Intensities || {})[resource];
  const dischargeCo2Intensity = (zoneData.dischargeCo2Intensities || {})[resource];
  const productionCo2Intensity = (zoneData.productionCo2Intensities || {})[resource];

  if (isStorage) {
    return storage > 0 ? storageCo2Intensity : dischargeCo2Intensity;
  }

  return productionCo2Intensity;
}

/**
 * Returns a link which maintains search and hash parameters
 * @param to
 */
export function createToWithState(to: string) {
  return `${to}${location.search}${location.hash}`;
}
