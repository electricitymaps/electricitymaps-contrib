import React, { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { values, size } from 'lodash';

export function useZoneGeometries() {
  const electricityMixMode = useSelector(state => state.application.electricityMixMode);
  const zones = useSelector(state => state.data.grid.zones);

  return useMemo(
    () => {
      const clickable = [];
      const nonClickable = [];

      values(zones).forEach((zone, zoneIndex) => {
        const feature = {
          type: 'Feature',
          geometry: {
            ...zone.geometry,
            coordinates: zone.geometry.coordinates.filter(size), // Remove empty geometries
          },
          properties: {
            zoneId: zoneIndex,
            co2intensity: electricityMixMode === 'consumption'
              ? zone.co2intensity
              : zone.co2intensityProduction,
          },
        };
        if (zone.isClickable === undefined || zone.isClickable === true) {
          clickable.push(feature);
        } else {
          nonClickable.push(feature);
        }
      });

      return { clickable, nonClickable };
    },
    [zones, electricityMixMode],
  );
}
