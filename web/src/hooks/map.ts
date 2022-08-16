import { useMemo } from 'react';
import { useSelector } from 'react-redux';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'loda... Remove this comment to see the full error message
import mapValues from 'lodash.mapvalues';

import { useCo2ColorScale } from './theme';

// TODO: Delete
export function useZonesWithColors() {
  const electricityMixMode = useSelector((state) => (state as any).application.electricityMixMode);
  const zones = useSelector((state) => (state as any).data.zones);
  const co2ColorScale = useCo2ColorScale();

  return useMemo(
    () =>
      mapValues(zones, (zone: any) => {
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
