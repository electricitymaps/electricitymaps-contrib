import generateTopos from 'features/map/map-utils/generateTopos';
import { useTheme } from 'hooks/theme';
import { useAtom } from 'jotai';
import { useMemo } from 'react';
import { MapGeometries } from 'types';
import { spatialAggregateAtom } from 'utils/state/atoms';

export const useGetGeometries = (): MapGeometries => {
  const [spatialAggregate] = useAtom(spatialAggregateAtom);
  const theme = useTheme();
  return useMemo(() => generateTopos(theme, spatialAggregate), [theme, spatialAggregate]);
};
