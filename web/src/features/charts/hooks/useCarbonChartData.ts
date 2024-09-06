import useGetZone from 'api/getZone';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { Mode } from 'utils/constants';
import { getCarbonIntensity } from 'utils/helpers';
import { productionConsumptionAtom } from 'utils/state/atoms';

import { AreaGraphElement } from '../types';

export function useCarbonChartData() {
  const { data, isLoading, isError } = useGetZone();
  const co2ColorScale = useCo2ColorScale();
  const mixMode = useAtomValue(productionConsumptionAtom);
  const isConsumption = mixMode === Mode.CONSUMPTION;

  if (isLoading || isError || !data) {
    return { isLoading, isError };
  }

  const chartData: AreaGraphElement[] = Object.entries(data.zoneStates).map(
    ([datetimeString, value]) => {
      const datetime = new Date(datetimeString);
      const carbonIntensity =
        getCarbonIntensity(
          {
            c: { ci: value.co2intensity },
            p: { ci: value.co2intensityProduction },
          },
          isConsumption
        ) || 0;

      return {
        datetime,
        layerData: {
          carbonIntensity,
        },
        meta: value,
      };
    }
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
