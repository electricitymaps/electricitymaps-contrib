import {
  ElectricityModeType,
  ElectricityStorageKeyType,
  GenerationType,
  ZoneDetail,
} from 'types';

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
export function getProductionCo2Intensity(
  mode: ElectricityModeType,
  zoneData: ZoneDetail
) {
  const isStorage = mode.includes('storage');
  const generationMode = mode.replace(' storage', '') as GenerationType;

  if (!isStorage) {
    return zoneData.productionCo2Intensities?.[generationMode];
  }

  const storageMode = generationMode as ElectricityStorageKeyType;
  const storage = zoneData.storage?.[storageMode];
  // If storing, we return 0 as we don't want to count it as CO2 emissions until electricity is discharged.
  if (storage && storage > 0) {
    return 0;
  }

  const dischargeCo2Intensity = zoneData.dischargeCo2Intensities?.[storageMode];
  return dischargeCo2Intensity;
}

/**
 * Returns a link which maintains search and hash parameters
 * @param to
 */
export function createToWithState(to: string) {
  return `${to}${location.search}${location.hash}`;
}

/**
 * Returns the fossil fuel percentage of a zone
 * @param isConsumption - Whether the percentage is for consumption or production
 * @param fossilFuelRatio - The fossil fuel ratio for consumption
 * @param fossilFuelRatioProduction - The fossil fuel ratio for production
 */
export function getFossilFuelPercentage(
  isConsumption: boolean,
  fossilFuelRatio: number | null | undefined,
  fossilFuelRatioProduction: number | null | undefined
): number {
  const fossilFuelRatioToUse = isConsumption
    ? fossilFuelRatio
    : fossilFuelRatioProduction;
  switch (fossilFuelRatioToUse) {
    case 0: {
      return 1;
    }
    case 1: {
      return 0;
    }
    case null:
    case undefined: {
      return Number.NaN;
    }
    default: {
      return 1 - fossilFuelRatioToUse;
    }
  }
}
