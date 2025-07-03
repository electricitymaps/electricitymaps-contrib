import useGetZone from 'api/getZone';
import { max as d3Max, min as d3Min } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { useAtomValue } from 'jotai';
import { scalePower } from 'utils/formatting';
import { round } from 'utils/helpers';
import { isFiveMinuteOrHourlyGranularityAtom } from 'utils/state/atoms';

import { AreaGraphElement } from '../types';

export function getFills(data: AreaGraphElement[]) {
  const values = Object.values(data).map((d) => d.layerData.load);
  const maxValue = d3Max<number>(values) ?? 0;
  const minValue = d3Min<number>(values) ?? 0;

  const colorScale = scaleLinear<string>()
    .domain([minValue, 0, maxValue])
    .range(['gray', 'lightgray', '#616161']);

  const layerFill = (key: string) => (d: { data: AreaGraphElement }) =>
    colorScale(d.data.layerData[key]);

  const markerFill = (key: string) => (d: { data: AreaGraphElement }) =>
    colorScale(d.data.layerData[key]);

  return { layerFill, markerFill };
}

export function useLoadChartData() {
  const { data: zoneData, isLoading, isError } = useGetZone();
  const isFineGranularity = useAtomValue(isFiveMinuteOrHourlyGranularityAtom);

  if (isLoading || isError || !zoneData) {
    return { isLoading, isError };
  }

  const chartData = Object.entries(zoneData.zoneStates).map(
    ([datetimeString, zoneDetail]) => ({
      datetime: new Date(datetimeString),
      layerData: {
        load: round(zoneDetail.totalConsumption),
      },
      meta: zoneDetail,
    })
  );

  const maxTotalValue = d3Max(chartData, (d) => d.layerData.load);
  const { unit, formattingFactor } = scalePower(maxTotalValue, isFineGranularity);
  const valueAxisLabel = unit;
  for (const d of chartData) {
    d.layerData.load /= formattingFactor;
  }

  const { layerFill, markerFill } = getFills(chartData);

  const layerKeys = ['load'];

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
