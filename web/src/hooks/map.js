import React, { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { forEach, size } from 'lodash';

export function useZoneGeometries() {
  const electricityMixMode = useSelector(state => state.application.electricityMixMode);
  const zones = useSelector(state => state.data.grid.zones);

  return useMemo(
    () => {
      const clickable = [];
      const nonClickable = [];

      forEach(zones, (zone, zoneId) => {
        const feature = {
          type: 'Feature',
          geometry: {
            ...zone.geometry,
            coordinates: zone.geometry.coordinates.filter(size), // Remove empty geometries
          },
          properties: {
            zoneId,
            zoneData: zone,
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
