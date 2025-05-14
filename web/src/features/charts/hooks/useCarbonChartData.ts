import useGetZone from 'api/getZone';
import { useColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { MapColorSource } from 'utils/constants';
import { getZoneValueForColor } from 'utils/helpers';
import { isConsumptionAtom } from 'utils/state/atoms';

import { AreaGraphElement } from '../types';

export function useCarbonChartData() {
  const { data, isLoading, isError } = useGetZone();
  const co2ColorScale = useColorScale();
  const isConsumption = useAtomValue(isConsumptionAtom);

  if (isLoading || isError || !data) {
    return { isLoading, isError };
  }

  const chartData: AreaGraphElement[] = Object.entries(data.zoneStates).map(
    ([datetimeString, value]) => ({
      datetime: new Date(datetimeString),
      layerData: {
        carbonIntensity:
          getZoneValueForColor(
            {
              c: { ci: value.co2intensity },
              p: { ci: value.co2intensityProduction },
            },
            isConsumption,
            MapColorSource.CARBON_INTENSITY
          ) || 0,
      },
      meta: value,
    })
  );

  const layerFill = (key: string) => (d: { data: AreaGraphElement }) => {
    if (d.data.layerData[key] === 0) {
      return co2ColorScale(Number.NaN);
    }
    return co2ColorScale(d.data.layerData[key]);
  };
  const result = {
    chartData,
    layerKeys: ['carbonIntensity'],
    layerFill,
  };

  return {
    data: result,
    isLoading,
    isError,
  };
}
