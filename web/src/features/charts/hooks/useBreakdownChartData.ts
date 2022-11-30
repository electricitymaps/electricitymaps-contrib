import useGetZone from 'api/getZone';
import { max as d3Max } from 'd3-array';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { ElectricityStorageType, ZoneDetail } from 'types';

import { Mode, modeColor, modeOrder } from 'utils/constants';
import { scalePower } from 'utils/formatting';
import { displayByEmissionsAtom, productionConsumptionAtom } from 'utils/state';
import { getGenerationTypeKey } from '../graphUtils';
import { AreaGraphElement } from '../types';

export const getLayerFill = (exchangeKeys: string[], co2ColorScale: any) => {
  const layerFill = (key: string) => {
    // If exchange layer, set the horizontal gradient by using a different fill for each datapoint.
    if (exchangeKeys.includes(key)) {
      return (d: { data: AreaGraphElement }) =>
        co2ColorScale((d.data.meta.exchangeCo2Intensities || {})[key]);
    }
    // Otherwise use regular production fill.
    return modeColor[key];
  };

  return layerFill;
};

export default function useBreakdownChartData() {
  const { data: zoneData, isLoading, isError } = useGetZone();
  const co2ColorScale = useCo2ColorScale();
  const [mixMode] = useAtom(productionConsumptionAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);

  if (isLoading || isError) {
    return { isLoading, isError };
  }

  const { valueFactor, valueAxisLabel } = getValuesInfo(
    Object.values(zoneData.zoneStates),
    displayByEmissions
  );

  const chartData: AreaGraphElement[] = [];
  const exchangeKeys: string[] = [];

  for (const [datetimeString, value] of Object.entries(zoneData.zoneStates)) {
    const datetime = new Date(datetimeString);
    const entry: AreaGraphElement = {
      datetime,
      meta: {
        exchangeCo2Intensities: value.exchangeCo2Intensities,
      },
      layerData: {},
    };

    for (const mode of modeOrder) {
      const isStorage = mode.includes('storage');

      if (isStorage) {
        entry.layerData[mode] = getStorageValue(
          mode,
          value,
          valueFactor,
          displayByEmissions
        );
        // TODO: handle storage
      } else {
        entry.layerData[mode] = getGenerationValue(
          mode,
          value,
          valueFactor,
          displayByEmissions
        );
      }
    }

    if (mixMode === Mode.CONSUMPTION) {
      // Add exchanges
      for (const [key, exchangeValue] of Object.entries(value.exchange)) {
        // in GW or MW
        entry.layerData[key] = Math.max(0, exchangeValue / valueFactor);
        if (displayByEmissions) {
          // in tCO₂eq/min
          entry.layerData[key] *= (value.exchangeCo2Intensities || {})[key] / 1e3 / 60;
        }

        // add exchange key to layerKeys if does not exist
        !exchangeKeys.includes(key) && exchangeKeys.push(key);
      }
    }
    chartData.push(entry);
  }

  const layerKeys: string[] = [...modeOrder, ...exchangeKeys];

  const result = {
    chartData,
    layerKeys,
    layerFill: getLayerFill(exchangeKeys, co2ColorScale),
    // markerFill,
    valueAxisLabel,
    layerStroke: undefined,
  };

  return { data: result, isLoading, isError };
}

function getStorageValue(
  key: string,
  value: ZoneDetail,
  valueFactor: number,
  displayByEmissions: boolean
) {
  const storageKey = key.replace(' storage', '') as ElectricityStorageType;
  let scaledValue = (-1 * Math.min(0, (value.storage || {})[storageKey])) / valueFactor;

  if (displayByEmissions) {
    scaledValue *= value.dischargeCo2Intensities[storageKey] / 1e3 / 60;
  }

  return scaledValue ?? Number.NaN;
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
  let scaledValue =
    modeProduction !== undefined ? modeProduction / valueFactor : undefined;

  if (displayByEmissions && scaledValue !== undefined) {
    scaledValue *= value.productionCo2Intensities[generationKey] / 1e3 / 60;
  }

  return scaledValue ?? Number.NaN;
}

interface ValuesInfo {
  valueAxisLabel: string; // For example, GW or tCO₂eq/min
  valueFactor: number; // TODO: why is this required
}

function getValuesInfo(
  historyData: ZoneDetail[],
  displayByEmissions: boolean
): ValuesInfo {
  const maxTotalValue = d3Max(
    historyData,
    (d: ZoneDetail) =>
      displayByEmissions
        ? (d.totalCo2Production + d.totalCo2Import + d.totalCo2Discharge) / 1e6 / 60 // in tCO₂eq/min
        : d.totalProduction + d.totalImport + d.totalDischarge // in MW
  );

  const format = scalePower(maxTotalValue);
  const valueAxisLabel = displayByEmissions ? 'tCO₂eq / min' : format.unit;
  const valueFactor = format.formattingFactor;
  return { valueAxisLabel, valueFactor };
}
