import useGetZone from 'api/getZone';
import { useCo2ColorScale } from 'hooks/theme';

import { useAtom } from 'jotai';
import { getCO2IntensityByMode } from 'utils/helpers';
import { productionConsumptionAtom } from 'utils/state/atoms';
import { AreaGraphElement } from '../types';

export function useCarbonChartData() {
  const { data, isLoading, isError } = useGetZone();
  const co2ColorScale = useCo2ColorScale();
  const [mixMode] = useAtom(productionConsumptionAtom);

  if (isLoading || isError) {
    return { isLoading, isError };
  }

  const chartData: AreaGraphElement[] = Object.entries(data.zoneStates).map(
    ([datetimeString, value]) => {
      const datetime = new Date(datetimeString);
      const carbonIntensity = getCO2IntensityByMode(
        {
          co2intensity: value.co2intensity || 0,
          co2intensityProduction: value.co2intensityProduction || 0,
        },
        mixMode
      );
      return {
        datetime,
        layerData: {
          carbonIntensity,
        },
        meta: value,
      };
    }
  );

  const layerFill = (key: string) => (d: { data: AreaGraphElement }) =>
    co2ColorScale(d.data.layerData[key]);

  const result = {
    chartData,
    layerKeys: ['carbonIntensity'],
    layerFill,
  };

  return { data: result, isLoading, isError };
}
