import generateTopos from 'features/map/map-utils/generateTopos';
import { useTheme } from 'hooks/theme';
import { useAtom } from 'jotai';
import { useMemo } from 'react';
import { MapGeometries, StatesGeometries } from 'types';
import { spatialAggregateAtom } from 'utils/state/atoms';

export const useGetGeometries = (): {
  worldGeometries: MapGeometries;
  statesGeometries: StatesGeometries;
} => {
  const [spatialAggregate] = useAtom(spatialAggregateAtom);
  const theme = useTheme();
  const { worldGeometries, statesGeometries } = useMemo(
    () => generateTopos(theme, spatialAggregate),
    [theme, spatialAggregate]
  );
  return { worldGeometries, statesGeometries };
};
