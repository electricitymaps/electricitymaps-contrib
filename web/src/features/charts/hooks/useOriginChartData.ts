import useGetZone from 'api/getZone';
import { max as d3Max } from 'd3-array';
import type { ScaleLinear } from 'd3-scale';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { useParams } from 'react-router-dom';
import {
  ElectricityModeType,
  ElectricityStorageKeyType,
  ElectricityStorageType,
  RouteParameters,
  ZoneDetail,
} from 'types';
import { modeColor, modeOrder, SpatialAggregate, TimeRange } from 'utils/constants';
import { scalePower } from 'utils/formatting';
import {
  displayByEmissionsAtom,
  isConsumptionAtom,
  spatialAggregateAtom,
  timeRangeAtom,
} from 'utils/state/atoms';

import { getExchangesToDisplay } from '../bar-breakdown/utils';
import {
  getGenerationTypeKey,
  getTotalElectricityAvailable,
  getTotalEmissionsAvailable,
} from '../graphUtils';
import { AreaGraphElement, LayerKey } from '../types';

export const getLayerFill =
  (co2ColorScale: ScaleLinear<string, string, string>) => (key: LayerKey) => {
    // Use regular production fill.
    if (key in modeColor) {
      return () => modeColor[key as ElectricityModeType];
    }
    // Otherwise it's an exchange, set the horizontal gradient by using a different fill for each datapoint.
    return (d: { data: AreaGraphElement }) =>
      co2ColorScale(d.data.meta.exchangeCo2Intensities?.[key]);
  };

export default function useOriginChartData() {
  const { data: zoneData, isLoading, isError } = useGetZone();
  const co2ColorScale = useCo2ColorScale();
  const { zoneId } = useParams<RouteParameters>();
  const isConsumption = useAtomValue(isConsumptionAtom);
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const viewMode = useAtomValue(spatialAggregateAtom);
  const timeAggregate = useAtomValue(timeRangeAtom);
  const isCountryView = viewMode === SpatialAggregate.COUNTRY;
  if (isLoading || isError || !zoneData || !zoneId) {
    return { isLoading, isError };
  }

  const exchangesForSelectedAggregate = getExchangesToDisplay(
    zoneId,
    isCountryView,
    zoneData.zoneStates
  );

  const { valueFactor, valueAxisLabel } = getValuesInfo(
    Object.values(zoneData.zoneStates),
    displayByEmissions,
    timeAggregate
  );

  const chartData: AreaGraphElement[] = [];
  const exchangeKeys: string[] = exchangesForSelectedAggregate;

  for (const [datetimeString, value] of Object.entries(zoneData.zoneStates)) {
    const datetime = new Date(datetimeString);
    const entry: AreaGraphElement = {
      datetime,
      meta: value,
      layerData: {},
    };

    for (const mode of modeOrder) {
      const isStorage = mode.includes('storage');

      // TODO: handle storage
      entry.layerData[mode] = isStorage
        ? getStorageValue(
            mode as ElectricityStorageType,
            value,
            valueFactor,
            displayByEmissions
          )
        : getGenerationValue(mode, value, valueFactor, displayByEmissions);
    }

    if (isConsumption) {
      // Add exchanges
      for (const [key, exchangeValue] of Object.entries(value.exchange)) {
        // in GW or MW
        entry.layerData[key] = Math.max(0, exchangeValue / valueFactor);
        if (displayByEmissions) {
          // in gCO₂eq/hour
          entry.layerData[key] =
            value.exchangeCo2Intensities?.[key] * Math.max(0, exchangeValue);
        }
      }
    }
    chartData.push(entry);
  }

  const layerKeys: string[] = [...modeOrder, ...exchangeKeys];

  // Ensure that all chart data entries contains all layer keys
  for (const entry of chartData) {
    for (const key of layerKeys) {
      if (!(key in entry.layerData)) {
        entry.layerData[key] = Number.NaN;
      }
    }
  }

  const result = {
    chartData,
    layerKeys,
    layerFill: getLayerFill(co2ColorScale),
    // markerFill,
    valueAxisLabel,
    layerStroke: undefined,
  };

  return {
    data: result,
    isLoading,
    isError,
  };
}

function getStorageValue(
  key: ElectricityStorageType,
  value: ZoneDetail,
  valueFactor: number,
  displayByEmissions: boolean
) {
  const storageKey = key.replace(' storage', '') as ElectricityStorageKeyType;
  const storageValue = value.storage?.[storageKey];
  if (storageValue === undefined || storageValue === null) {
    return Number.NaN;
  }

  const invertedValue = -1 * Math.min(0, storageValue);

  return displayByEmissions
    ? invertedValue * value.dischargeCo2Intensities[storageKey] * valueFactor
    : invertedValue / valueFactor;
}

function getGenerationValue(
  key: string,
  value: ZoneDetail,
  valueFactor: number,
  displayByEmissions: boolean
) {
  const generationKey = getGenerationTypeKey(key);
  if (generationKey === undefined) {
    return Number.NaN;
  }

  const modeProduction = value.production[generationKey];

  if (modeProduction === undefined || modeProduction === null) {
    return Number.NaN;
  }

  return displayByEmissions
    ? modeProduction * value.productionCo2Intensities[generationKey] * valueFactor
    : modeProduction / valueFactor;
}

interface ValuesInfo {
  valueAxisLabel: string; // For example, GW or CO₂eq
  valueFactor: number;
}

function getValuesInfo(
  historyData: ZoneDetail[],
  displayByEmissions: boolean,
  timeAggregate: string
): ValuesInfo {
  const maxTotalValue = d3Max(historyData, (d: ZoneDetail) =>
    displayByEmissions
      ? getTotalEmissionsAvailable(d, true)
      : getTotalElectricityAvailable(d, true)
  );
  const isHourly = timeAggregate === TimeRange.H24;
  const format = displayByEmissions
    ? // Value factor of 1000 to convert from MW to KW
      { formattingFactor: 1000, unit: 'CO₂eq' }
    : scalePower(maxTotalValue, isHourly);
  const valueAxisLabel = format.unit;
  const valueFactor = format.formattingFactor;
  return { valueAxisLabel, valueFactor };
}
