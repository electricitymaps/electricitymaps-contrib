import { useMemo } from 'react';

import { AreaGraphElement } from '../types';

export const useEstimationData = (chartData?: AreaGraphElement[]) =>
  useMemo(() => {
    if (!chartData) {
      return {
        estimated: undefined,
        estimationMethod: undefined,
        someEstimated: undefined,
      };
    }
    const estimated = chartData.map((d) => {
      const { estimationMethod } = d.meta;
      return Boolean(estimationMethod);
    });
    const estimationMethod = chartData.find((d) => d.meta.estimationMethod)?.meta
      .estimationMethod;
    const someEstimated = estimated.some(Boolean);
    return { estimated, estimationMethod, someEstimated };
  }, [chartData]);
