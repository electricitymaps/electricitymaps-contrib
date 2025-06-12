import { max as d3Max } from 'd3-array';
import {
  ElectricityModeType,
  ElectricityStorageKeyType,
  GenerationType,
  Maybe,
  ZoneDetail,
  ZoneKey,
} from 'types';
import { modeOrderBarBreakdown } from 'utils/constants';
import { getProductionCo2Intensity } from 'utils/helpers';
import { EnergyUnits } from 'utils/units';

import exchangesToExclude from '../../../../config/excluded_aggregated_exchanges.json';

const LABEL_MAX_WIDTH = 102;
const ROW_HEIGHT = 13;
const PADDING_Y = 7;
const PADDING_X = 5;
const X_AXIS_HEIGHT = 15;
const DEFAULT_FLAG_SIZE = 16;

export function getExchangeCo2Intensity(
  zoneKey: ZoneKey,
  zoneData: ZoneDetail,
  isConsumption: boolean
) {
  const exchange = zoneData.exchange?.[zoneKey];
  const exchangeCo2Intensity = zoneData.exchangeCo2Intensities?.[zoneKey];

  if (exchange != null && exchange >= 0) {
    return exchangeCo2Intensity;
  }

  // We don't use getCO2IntensityByMode in order to more easily return 0 for invalid numbers
  if (isConsumption) {
    return zoneData.co2intensity || 0;
  }

  return zoneData.co2intensityProduction || 0;
}

export interface ProductionDataType {
  production: Maybe<number>;
  capacity: Maybe<number>;
  isStorage: boolean;
  storage: Maybe<number>;
  mode: ElectricityModeType;
  gCo2eq: number;
}

export const getProductionData = (data?: ZoneDetail): ProductionDataType[] => {
  if (!data) {
    return [];
  }
  return modeOrderBarBreakdown.map((mode) => {
    const isStorage = mode.includes('storage');
    const generationMode = mode.replace(' storage', '') as GenerationType;
    // Power in MW

    const capacity = data.capacity?.[mode];
    const production = data.production?.[generationMode];
    const storage = data.storage?.[generationMode as ElectricityStorageKeyType];

    // Production CO₂ intensity
    const gCo2eqPerkWh = getProductionCo2Intensity(mode, data);
    const value = isStorage ? storage : production || 0;
    const gCo2eq = gCo2eqPerkWh * 1000 * (value || 0);

    return {
      isStorage,
      storage,
      production,
      capacity,
      mode,
      gCo2eq,
    };
  });
};
interface GetElectricityProductionValueType {
  capacity: Maybe<number>;
  isStorage: boolean;
  production: Maybe<number>;
  storage: Maybe<number>;
}
export function getElectricityProductionValue({
  capacity,
  isStorage,
  production,
  storage,
}: GetElectricityProductionValueType) {
  const value = isStorage ? storage : production;

  // If the value is not defined but the capacity
  // is zero, assume the value is also zero.
  if (!Number.isFinite(value) && capacity === 0) {
    return 0;
  }

  if (!isStorage) {
    return value;
  }

  // Handle storage scenarios
  if (storage === null || storage === undefined) {
    return null;
  }
  // Do not negate value if it is zero
  return storage === 0 ? 0 : -storage;
}

export const getDataBlockPositions = (
  productionLength: number,
  exchangeData: ExchangeDataType[]
) => {
  const productionHeight = productionLength * (ROW_HEIGHT + PADDING_Y);
  const productionY = X_AXIS_HEIGHT + PADDING_Y;

  const exchangeMax = d3Max(exchangeData, (d) => d.zoneKey.length) || 0;

  const exchangeFlagX =
    LABEL_MAX_WIDTH - 4 * PADDING_X - DEFAULT_FLAG_SIZE - exchangeMax * 8;
  const exchangeHeight = exchangeData.length * (ROW_HEIGHT + PADDING_Y);
  const exchangeY = productionY + productionHeight;

  return {
    productionHeight,
    productionY,
    exchangeFlagX,
    exchangeHeight,
    exchangeY,
  };
};

export interface ExchangeDataType {
  exchange: number | null;
  zoneKey: ZoneKey;
  gCo2eqPerkWh: number | null;
  gCo2eq: number;
  exchangeCapacityRange: number[];
}
export const getExchangeData = (
  exchangeKeys: ZoneKey[],
  isConsumption: boolean,
  data?: ZoneDetail
): ExchangeDataType[] => {
  if (!data || !isConsumption) {
    return [];
  }
  return exchangeKeys.map((zoneKey: ZoneKey) => {
    // Power in MW
    const exchange = data.exchange?.[zoneKey];
    const exchangeCapacityRange = data.exchangeCapacities?.[zoneKey] ?? [0, 0];

    // Exchange CO₂ intensity
    const gCo2eqPerkWh = getExchangeCo2Intensity(zoneKey, data, isConsumption);
    const gCo2eq =
      gCo2eqPerkWh == null || exchange == null
        ? Number.NaN
        : gCo2eqPerkWh * 1000 * exchange;

    return {
      exchange,
      exchangeCapacityRange,
      zoneKey,
      gCo2eqPerkWh,
      gCo2eq,
    };
  });
};

export const getExchangesToDisplay = (
  isCountryView: boolean,
  currentZoneKey?: ZoneKey,
  zoneStates?: {
    [key: string]: ZoneDetail;
  }
): ZoneKey[] => {
  if (!currentZoneKey || !zoneStates) {
    return [];
  }

  const exchangeKeysToRemove = isCountryView
    ? exchangesToExclude.exchangesToExcludeCountryView
    : exchangesToExclude.exchangesToExcludeZoneView;

  const exchangeZoneKeysToRemove = new Set(
    exchangeKeysToRemove.flatMap((exchangeKey) => {
      const split = exchangeKey.split('->');
      if (split.includes(currentZoneKey)) {
        return split.filter((exchangeKey) => exchangeKey !== currentZoneKey);
      }
      return [];
    })
  );

  // get all exchanges for the given period
  const allExchangeKeys = new Set<string>();
  for (const state of Object.values(zoneStates)) {
    for (const key of Object.keys(state.exchange)) {
      allExchangeKeys.add(key);
    }
  }
  const uniqueExchangeKeys = [...allExchangeKeys];

  return uniqueExchangeKeys.filter(
    (exchangeZoneKey) => !exchangeZoneKeysToRemove.has(exchangeZoneKey)
  );
};

/**
 * Convents the price value and unit to the correct value and unit for the matching currency.
 *
 * If no currency is provided, the parameters are returned as is.
 */
export const convertPrice = (
  value?: number,
  currency?: string,
  unit: EnergyUnits = EnergyUnits.MEGAWATT_HOURS
): { value?: number; currency?: string; unit: EnergyUnits } => ({
  value,
  currency,
  unit,
});
