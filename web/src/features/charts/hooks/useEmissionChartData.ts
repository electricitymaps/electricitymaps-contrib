import useGetZone from 'api/getZone';
import { max as d3Max } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { useAtomValue } from 'jotai';
import { isConsumptionAtom } from 'utils/state/atoms';

import { getTotalEmissionsAvailable } from '../graphUtils';
import { AreaGraphElement } from '../types';

export function useEmissionChartData() {
  const { data, isLoading, isError } = useGetZone();
  const isConsumption = useAtomValue(isConsumptionAtom);

  if (isLoading || isError || !data) {
    return { isLoading, isError };
  }

  const chartData: AreaGraphElement[] = Object.entries(data.zoneStates).map(
    ([datetimeString, value]) => ({
      datetime: new Date(datetimeString),
      layerData: {
        emissions: getTotalEmissionsAvailable(value, isConsumption),
      },
      meta: value,
    })
  );

  const maxEmissions =
    d3Max(chartData.map((d: AreaGraphElement) => d.layerData.emissions || 0)) || 0;
  const emissionsColorScale = scaleLinear<string>()
    .domain([0, maxEmissions])
    .range(['yellow', 'brown']);

  const layerKeys = ['emissions'];
  const layerFill = (key: string) => (d: { data: AreaGraphElement }) =>
    emissionsColorScale(d.data.layerData[key]);

  const result = {
    chartData,
    layerKeys,
    layerFill,
    layerStroke: undefined,
  };

  return {
    data: result,
    isLoading,
    isError,
  };
}
