import { callerLocation, useMeta } from 'api/getMeta';
import { useCallback } from 'react';
import {
  useLocation,
  useMatch,
  useMatches,
  useNavigate,
  useParams,
} from 'react-router-dom';
import {
  ElectricityModeType,
  ElectricityStorageKeyType,
  GenerationType,
  RouteParameters,
  StateZoneData,
  ZoneDetail,
} from 'types';

import zonesConfigJSON from '../../config/zones.json';
import { CombinedZonesConfig } from '../../geo/types';
import { historicalTimeRange, TimeRange } from './constants';

export function useGetZoneFromPath() {
  const { zoneId } = useParams<RouteParameters>();
  const match = useMatch('/zone/:id');
  if (zoneId) {
    return zoneId;
  }
  return match?.params.id || undefined;
}

export function useUserLocation(): callerLocation {
  const { callerLocation } = useMeta();
  if (
    callerLocation &&
    callerLocation.length === 2 &&
    callerLocation.every((x) => Number.isFinite(x))
  ) {
    return callerLocation;
  }
  return null;
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

export function useNavigateWithParameters() {
  const navigator = useNavigate();
  const location = useLocation();
  const {
    zoneId: previousZoneId,
    urlTimeRange: previousTimeRange,
    urlDatetime: previousDatetime,
    resolution: previousResolution,
  } = useParams();
  const parameters = useMatches();
  const isZoneRoute = parameters.some((match) => match.pathname.startsWith('/zone'));

  const basePath = isZoneRoute ? '/zone' : '/map';

  return useCallback(
    ({
      to = basePath,
      zoneId = isZoneRoute ? previousZoneId : undefined,
      timeRange = previousTimeRange as TimeRange,
      datetime = previousDatetime,
      keepHashParameters = true,
      resolution = previousResolution,
    }: {
      to?: string;
      zoneId?: string;
      timeRange?: TimeRange;
      datetime?: string;
      keepHashParameters?: boolean;
      resolution?: string;
    }) => {
      // Always preserve existing search params
      const isDestinationZoneRoute = to.startsWith('/zone');
      const currentSearch = new URLSearchParams(location.search);
      const path = getDestinationPath({
        to,
        zoneId: isDestinationZoneRoute ? zoneId : undefined,
        timeRange: timeRange.includes('all') ? 'all' : timeRange,
        datetime,
        resolution,
      });
      const fullPath = {
        pathname: path,
        search: currentSearch.toString() ? `?${currentSearch.toString()}` : '',
        hash: keepHashParameters ? location.hash : undefined,
      };
      console.log('fullPath', fullPath);
      navigator(fullPath);
    },
    [
      basePath,
      isZoneRoute,
      location.hash,
      location.search,
      navigator,
      previousDatetime,
      previousResolution,
      previousTimeRange,
      previousZoneId,
    ]
  );
}

export function getDestinationPath({
  to,
  zoneId,
  timeRange,
  datetime,
  resolution,
}: {
  to: string;
  zoneId?: string;
  timeRange?: TimeRange | 'all';
  datetime?: string;
  resolution?: string;
}) {
  console.log(timeRange);
  return `${to}${zoneId ? `/${zoneId}` : ''}${timeRange ? `/${timeRange}` : ''}${
    resolution ? `/${resolution}` : ''
  }${datetime ? `/${datetime}` : ''}`;
}

/**
 * Returns the fossil fuel ratio of a zone
 * @param isConsumption - Whether the ratio is for consumption or production
 * @param fossilFuelRatio - The fossil fuel ratio for consumption
 * @param fossilFuelRatioProduction - The fossil fuel ratio for production
 */
export function getFossilFuelRatio(
  zoneData: StateZoneData,
  isConsumption: boolean
): number {
  const fossilFuelRatioToUse = isConsumption ? zoneData?.c?.fr : zoneData?.p?.fr;
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
export const getCarbonIntensity = (
  zoneData: StateZoneData,
  isConsumption: boolean
): number => (isConsumption ? zoneData?.c?.ci : zoneData?.p?.ci) ?? Number.NaN;

/**
 * Returns the renewable ratio of a zone
 * @param zoneData - The zone data
 * @param isConsumption - Whether the ratio is for consumption or production
 */
export const getRenewableRatio = (
  zoneData: StateZoneData,
  isConsumption: boolean
): number => (isConsumption ? zoneData?.c?.rr : zoneData?.p?.rr) ?? Number.NaN;

/**
 * Function to round a number to a specific amount of decimals.
 * @param {number} number - The number to round.
 * @param {number} decimals - Defaults to 2 decimals.
 * @returns {number} Rounded number.
 */
export const round = (number: number, decimals = 2): number =>
  (Math.round((Math.abs(number) + Number.EPSILON) * 10 ** decimals) / 10 ** decimals) *
  Math.sign(number);

/**
 * Returns the net exchange of a zone
 * @param zoneData - The zone data
 * @returns The net exchange
 */
export function getNetExchange(
  zoneData: ZoneDetail,
  displayByEmissions: boolean
): number {
  if (
    !displayByEmissions &&
    zoneData.totalImport === null &&
    zoneData.totalExport === null
  ) {
    return Number.NaN;
  }
  if (
    displayByEmissions &&
    zoneData.totalCo2Import == null &&
    zoneData.totalCo2Export == null
  ) {
    return Number.NaN;
  }

  const netExchangeValue = displayByEmissions
    ? round((zoneData.totalCo2Import ?? 0) - (zoneData.totalCo2Export ?? 0)) // in CO₂eq
    : round((zoneData.totalImport ?? 0) - (zoneData.totalExport ?? 0));

  return netExchangeValue;
}

export const getZoneTimezone = (zoneId?: string) => {
  if (!zoneId) {
    return undefined;
  }
  const { zones } = zonesConfigJSON as unknown as CombinedZonesConfig;
  return zones[zoneId]?.timezone;
};

const MOBILE_USER_AGENT_PATTERN: RegExp =
  /android|blackberry|iemobile|ipad|iphone|ipod|opera mini|webos/i;
/**
 * @returns {Boolean} true if agent is probably a mobile device.
 */
export const hasMobileUserAgent = () =>
  MOBILE_USER_AGENT_PATTERN.test(navigator.userAgent);

export const isValidHistoricalTimeRange = (timeRange: TimeRange) =>
  historicalTimeRange.includes(timeRange);

export const getLocalTime = (date: Date, timezone?: string) => {
  if (!timezone) {
    return { localHours: date.getUTCHours(), localMinutes: date.getUTCMinutes() };
  }

  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    hour: 'numeric',
    minute: 'numeric',
    hour12: false,
  });

  const [hours, minutes] = formatter
    .format(date)
    .split(':')
    .map((n) => Number.parseInt(n, 10));

  return { localHours: hours, localMinutes: minutes };
};
