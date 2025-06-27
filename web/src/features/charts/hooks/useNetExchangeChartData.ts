import useGetZone from 'api/getZone';
import { max as d3Max, min as d3Min } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { useAtomValue } from 'jotai';
import { ZoneDetail } from 'types';
import { scalePower } from 'utils/formatting';
import { getNetExchange, round } from 'utils/helpers';
import { displayByEmissionsAtom, isFineGranularityAtom } from 'utils/state/atoms';

import { AreaGraphElement } from '../types';

export function getFills(data: AreaGraphElement[]) {
  const netExchanges = Object.values(data).map((d) => d.layerData.netExchange);
  const netExchangeMaxValue = d3Max<number>(netExchanges) ?? 0;
  const netExchangeMinValue = d3Min<number>(netExchanges) ?? 0;

  const netExchangeColorScale = scaleLinear<string>()
    .domain([netExchangeMinValue, 0, netExchangeMaxValue])
    .range(['gray', 'lightgray', '#616161']);

  const layerFill = (key: string) => (d: { data: AreaGraphElement }) =>
    netExchangeColorScale(d.data.layerData[key]);

  const markerFill = (key: string) => (d: { data: AreaGraphElement }) =>
    netExchangeColorScale(d.data.layerData[key]);

  return { layerFill, markerFill };
}

export function useNetExchangeChartData() {
  const { data: zoneData, isLoading, isError } = useGetZone();
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const isFineGranularity = useAtomValue(isFineGranularityAtom);

  if (isLoading || isError || !zoneData) {
    return { isLoading, isError };
  }

  const { valueFactor, valueAxisLabel } = getValuesInfo(
    Object.values(zoneData.zoneStates),
    displayByEmissions,
    isFineGranularity
  );

  const chartData = Object.entries(zoneData.zoneStates).map(
    ([datetimeString, zoneDetail]) => ({
      datetime: new Date(datetimeString),
      layerData: {
        netExchange: round(getNetExchange(zoneDetail, displayByEmissions) / valueFactor),
      },
      meta: zoneDetail,
    })
  );

  const { layerFill, markerFill } = getFills(chartData);

  const layerKeys = ['netExchange'];

  const result = {
    chartData,
    layerKeys,
    layerFill,
    markerFill,
    valueAxisLabel,
    layerStroke: undefined,
  };

  return { data: result, isLoading, isError };
}

interface ValuesInfo {
  valueAxisLabel: string; // For example, GW or CO₂eq
  valueFactor: number;
}

function getValuesInfo(
  historyData: ZoneDetail[],
  displayByEmissions: boolean,
  isFineGranularity: boolean
): ValuesInfo {
  const maxTotalValue = d3Max(historyData, (d: ZoneDetail) =>
    Math.abs(getNetExchange(d, displayByEmissions))
  );

  const { unit, formattingFactor } = displayByEmissions
    ? {
        unit: 'CO₂eq',
        formattingFactor: 1,
      }
    : scalePower(maxTotalValue, isFineGranularity);
  const valueAxisLabel = unit;
  const valueFactor = formattingFactor;

  return { valueAxisLabel, valueFactor };
}
