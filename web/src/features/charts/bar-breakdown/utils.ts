import { max as d3Max } from 'd3-array';
import {
  ElectricityModeType,
  ElectricityStorageKeyType,
  Exchange,
  GenerationType,
  Maybe,
  ZoneDetail,
  ZoneKey,
} from 'types';
import { Mode, modeOrder } from 'utils/constants';
import { getCO2IntensityByMode } from 'utils/helpers';
import exchangesToExclude from '../../../../config/excludedAggregatedExchanges.json'; // TODO: do something globally

const LABEL_MAX_WIDTH = 102;
const ROW_HEIGHT = 13;
const PADDING_Y = 7;
const PADDING_X = 5;
const X_AXIS_HEIGHT = 15;
const DEFAULT_FLAG_SIZE = 16;

export function getProductionCo2Intensity(
  mode: ElectricityModeType,
  zoneData: ZoneDetail
) {
  const isStorage = mode.includes('storage');
  const generationMode = mode.replace(' storage', '') as GenerationType;

  if (!isStorage) {
    return zoneData.productionCo2Intensities?.[generationMode];
  }

  const storage = zoneData.storage?.[generationMode as ElectricityStorageKeyType];
  // TODO: Find out how this worked before if the data is never available
  const storageCo2Intensity = zoneData.storageCo2Intensities?.[generationMode];
  const dischargeCo2Intensity =
    zoneData.dischargeCo2Intensities?.[generationMode as ElectricityStorageKeyType];

  return storage && storage > 0 ? storageCo2Intensity : dischargeCo2Intensity;
}

export function getExchangeCo2Intensity(mode, zoneData, electricityMixMode) {
  const exchange = (zoneData.exchange || {})[mode];
  const exchangeCo2Intensity = (zoneData.exchangeCo2Intensities || {})[mode];

  if (exchange >= 0) {
    return exchangeCo2Intensity;
  }

  return getCO2IntensityByMode(zoneData, electricityMixMode);
}

export interface ProductionDataType {
  production: Maybe<number>;
  capacity: Maybe<number>;
  isStorage: boolean;
  storage: Maybe<number>;
  mode: ElectricityModeType;
  tCo2eqPerMin: number;
}

export const getProductionData = (data: ZoneDetail): ProductionDataType[] =>
  modeOrder.map((mode) => {
    const isStorage = mode.includes('storage');
    const generationMode = mode.replace(' storage', '') as GenerationType;
    // Power in MW

    const capacity = data.capacity?.[mode];
    const production = data.production?.[generationMode];
    const storage = data.storage?.[generationMode as ElectricityStorageKeyType];

    // Production CO₂ intensity
    const gCo2eqPerkWh = getProductionCo2Intensity(mode, data);
    const value = isStorage && storage ? storage : production || 0;
    const gCo2eqPerHour = gCo2eqPerkWh * 1e3 * value;
    const tCo2eqPerMin = gCo2eqPerHour / 1e6 / 60;

    return {
      isStorage,
      storage,
      production,
      capacity,
      mode,
      tCo2eqPerMin,
    };
  });

interface GetElectricityProductionValueType {
  capacity: number;
  isStorage: boolean;
  production: number;
  storage: number;
}
export function getElectricityProductionValue({
  capacity,
  isStorage,
  production,
  storage,
}: GetElectricityProductionValueType) {
  const value = isStorage ? -storage : production;
  // If the value is not defined but the capacity
  // is zero, assume the value is also zero.
  if (!Number.isFinite(value) && capacity === 0) {
    return 0;
  }
  return value;
}

export const getDataBlockPositions = (
  prouductionLength: number,
  exchangeData: ExchangeDataType[]
) => {
  const productionHeight = prouductionLength * (ROW_HEIGHT + PADDING_Y);
  const productionY = X_AXIS_HEIGHT + PADDING_Y;

  const exchangeMax = d3Max(exchangeData, (d) => d.mode.length) || 0;

  const exchangeFlagX =
    LABEL_MAX_WIDTH - 4 * PADDING_X - DEFAULT_FLAG_SIZE - exchangeMax * 8;
  const exchangeHeight = exchangeData.length * (ROW_HEIGHT + PADDING_Y);
  const exchangeY = productionY + productionHeight + ROW_HEIGHT + PADDING_Y;

  return {
    productionHeight,
    productionY,
    exchangeFlagX,
    exchangeHeight,
    exchangeY,
  };
};

export interface ExchangeDataType {
  exchange: number;
  mode: ZoneKey; // TODO: Weird that this is called "mode"
  gCo2eqPerkWh: number;
  tCo2eqPerMin: number;
}
export const getExchangeData = (
  data: ZoneDetail,
  exchangeKeys: string[],
  electricityMixMode: Mode
): ExchangeDataType[] =>
  exchangeKeys.map((mode) => {
    // Power in MW
    const exchange = (data.exchange || {})[mode];
    const exchangeCapacityRange = (data.exchangeCapacities || {})[mode];

    // Exchange CO₂ intensity
    const gCo2eqPerkWh = getExchangeCo2Intensity(mode, data, electricityMixMode);
    const gCo2eqPerHour = gCo2eqPerkWh * 1e3 * exchange;
    const tCo2eqPerMin = gCo2eqPerHour / 1e6 / 60;

    return {
      exchange,
      exchangeCapacityRange,
      mode,
      gCo2eqPerkWh,
      tCo2eqPerMin,
    };
  });

export const getExchangesToDisplay = (
  currentZoneKey: ZoneKey,
  isAggregatedToggled: boolean,
  exchangeZoneKeysForCurrentZone: Exchange
): ZoneKey[] => {
  const exchangeKeysToRemove = isAggregatedToggled
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

  const currentExchanges = Object.keys(exchangeZoneKeysForCurrentZone);
  return currentExchanges
    ? currentExchanges.filter(
        (exchangeZoneKey) => !exchangeZoneKeysToRemove.has(exchangeZoneKey)
      )
    : [];
};
