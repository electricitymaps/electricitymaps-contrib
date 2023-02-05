import useGetZone from 'api/getZone';
import { max as d3Max } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { useAtom } from 'jotai';
import { Mode } from 'utils/constants';
import { productionConsumptionAtom } from 'utils/state/atoms';
import { getTotalElectricity, tonsPerHourToGramsPerMinute } from '../graphUtils';
import { AreaGraphElement } from '../types';

export function useEmissionChartData() {
  const { data, isLoading, isError } = useGetZone();
  const [mixMode] = useAtom(productionConsumptionAtom);

  if (isLoading || isError) {
    return { isLoading, isError };
  }

  const chartData: AreaGraphElement[] = Object.entries(data.zoneStates).map(
    ([datetimeString, value]) => {
      const datetime = new Date(datetimeString);
      return {
        datetime,
        layerData: {
          emissions: tonsPerHourToGramsPerMinute(
            getTotalElectricity(value, mixMode === Mode.CONSUMPTION)
          ),
        },
        meta: value,
      };
    }
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

  return { data: result, isLoading, isError };
}
