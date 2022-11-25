import useGetZone from 'api/getZone';
import { max as d3Max } from 'd3-array';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { ZoneDetail } from 'types';

import { Mode, modeColor, modeOrder } from 'utils/constants';
import { scalePower } from 'utils/formatting';
import { productionConsumptionAtom } from 'utils/state';
import { getGenerationTypeKey, getStorageKey } from '../graphUtils';
import { AreaGraphElement } from '../types';

export default function useBreakdownChartDatas() {
  const { data: zoneData, isLoading, isError } = useGetZone();
  const co2ColorScale = useCo2ColorScale();
  const [mixMode] = useAtom(productionConsumptionAtom);
  const displayByEmissions = false;

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
        entry.layerData[mode] = 0;
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
        if (
          Number.isFinite(value) &&
          displayByEmissions &&
          entry.layerData[key] != undefined
        ) {
          // in tCO₂eq/min
          entry.layerData[key] *= (value.exchangeCo2Intensities || {})[key] / 1e3 / 60;
        }

        // add exchange key to layerKeys if does not exist
        !exchangeKeys.includes(key) && exchangeKeys.push(key);
      }
    }

    chartData.push(entry);
  }

  const layerFill = (key: string) => {
    // If exchange layer, set the horizontal gradient by using a different fill for each datapoint.
    if (exchangeKeys.includes(key)) {
      return (d: { data: AreaGraphElement }) =>
        co2ColorScale((d.data.meta.exchangeCo2Intensities || {})[key]);
    }
    // Otherwise use regular production fill.
    return modeColor[key];
  };

  const layerKeys: string[] = [...modeOrder, ...exchangeKeys];

  const result = {
    chartData,
    layerKeys,
    layerFill,
    // markerFill,
    valueAxisLabel,
    layerStroke: undefined,
  };

  return { data: result, isLoading, isError };
}

function getStorageValue(key: string, value: ZoneDetail) {
  const storageKey = getStorageKey(key);
  if (storageKey !== undefined) {
    return -1 * Math.min(0, (value.storage || {})[storageKey]);
  }
}

function getGenerationValue(
  key: string,
  value: ZoneDetail,
  valueFactor: number,
  displayByEmissions: boolean
) {
  const generationKey = getGenerationTypeKey(key);
  if (generationKey === undefined) {
    return 0;
  }

  const modeProduction = value.production[generationKey];
  let temporary = modeProduction !== undefined ? modeProduction / valueFactor : undefined;

  if (displayByEmissions) {
    temporary *= value.productionCo2Intensities[generationKey] / 1e3 / 60;
  }

  return temporary || 0;
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
