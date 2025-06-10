import { useMemo } from 'react';
import { round } from 'utils/helpers';

export const useEstimationData = (chartData?: any[]) =>
  useMemo(() => {
    if (!chartData) {
      return {
        estimated: undefined,
        estimationMethod: undefined,
        someEstimated: undefined,
      };
    }
    const estimated = chartData.map((d: any) => {
      const { estimationMethod, estimatedPercentage } = d.meta;
      const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
      return estimationMethod != undefined || Boolean(roundedEstimatedPercentage);
    });
    const estimationMethod = chartData.find((d: any) => d.meta.estimationMethod)?.meta
      .estimationMethod;
    const someEstimated = estimated.some(Boolean);
    return { estimated, estimationMethod, someEstimated };
  }, [chartData]);
