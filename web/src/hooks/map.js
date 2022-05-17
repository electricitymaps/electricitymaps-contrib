import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import mapValues from 'lodash.mapvalues';

import { useCo2ColorScale } from './theme';

export function useZonesWithColors() {
  const electricityMixMode = useSelector((state) => state.application.electricityMixMode);
  const zones = useSelector((state) => state.data.grid.zones);
  const co2ColorScale = useCo2ColorScale();

  return useMemo(
    () =>
      mapValues(zones, (zone) => {
        const co2intensity = electricityMixMode === 'consumption' ? zone.co2intensity : zone.co2intensityProduction;
        return {
          ...zone,
          color: Number.isFinite(co2intensity) ? co2ColorScale(co2intensity) : undefined,
          isClickable: true,
        };
      }),
    [zones, electricityMixMode, co2ColorScale]
  );
}
