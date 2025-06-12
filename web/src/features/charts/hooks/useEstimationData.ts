import { useMemo } from 'react';

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
      const { estimationMethod } = d.meta;
      return Boolean(estimationMethod);
    });
    const estimationMethod = chartData.find((d: any) => d.meta.estimationMethod)?.meta
      .estimationMethod;
    const someEstimated = estimated.some(Boolean);
    return { estimated, estimationMethod, someEstimated };
  }, [chartData]);
