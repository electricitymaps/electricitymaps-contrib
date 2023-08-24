import {
  ElectricityModeType,
  ElectricityStorageKeyType,
  GenerationType,
  ZoneDetail,
} from 'types';
import { useParams, useMatch } from 'react-router-dom';

export function getZoneFromPath() {
  const { zoneId } = useParams();
  if (zoneId) {
    return zoneId;
  }
  const match = useMatch('/zone/:id');
  return match?.params.id || undefined;
}

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
 * Returns the fossil fuel ratio of a zone
 * @param isConsumption - Whether the ratio is for consumption or production
 * @param fossilFuelRatio - The fossil fuel ratio for consumption
 * @param fossilFuelRatioProduction - The fossil fuel ratio for production
 */
export function getFossilFuelRatio(
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

/**
 * Returns the carbon intensity of a zone
 * @param isConsumption - Whether the percentage is for consumption or production
 * @param co2intensity - The carbon intensity for consumption
 * @param co2intensityProduction - The carbon intensity for production
 */
export function getCarbonIntensity(
  isConsumption: boolean,
  co2intensity: number | null | undefined,
  co2intensityProduction: number | null | undefined
): number {
  return (isConsumption ? co2intensity : co2intensityProduction) ?? Number.NaN;
}

/**
 * Returns the renewable ratio of a zone
 * @param isConsumption - Whether the ratio is for consumption or production
 * @param renewableRatio - The renewable ratio for consumption
 * @param renewableRatioProduction - The renewable ratio for production
 */
export function getRenewableRatio(
  isConsumption: boolean,
  renewableRatio: number | null | undefined,
  renewableRatioProduction: number | null | undefined
): number {
  return (isConsumption ? renewableRatio : renewableRatioProduction) ?? Number.NaN;
}

/**
 * Function to round a number to a specific amount of decimals.
 * @param {number} number - The number to round.
 * @param {number} decimals - Defaults to 2 decimals.
 * @returns {number} Rounded number.
 */
export const round = (number: number, decimals = 2): number => {
  return (
    (Math.round((Math.abs(number) + Number.EPSILON) * 10 ** decimals) / 10 ** decimals) *
    Math.sign(number)
  );
};

/**
 * Returns the net exchange of a zone
 * @param zoneData - The zone data
 * @returns The net exchange
 */
export function getNetExchange(
  zoneData: ZoneDetail,
  displayByEmissions: boolean
): number {
  if (Object.keys(zoneData.exchange).length === 0) {
    return Number.NaN;
  }
  return displayByEmissions
    ? round(zoneData.totalCo2NetExchange / 1e6 / 60) // in tCO₂eq/min
    : round(zoneData.totalImport - zoneData.totalExport);
}
