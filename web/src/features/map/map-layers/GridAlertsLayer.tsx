import useGetState from 'api/getState';
import { getTextColor } from 'components/CarbonIntensitySquare';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { useMemo } from 'react';
import { FiAlertTriangle } from 'react-icons/fi';
import { Marker } from 'react-map-gl/maplibre';
import { GridState, MapGeometries } from 'types';
import { getCarbonIntensity } from 'utils/helpers';
import { isConsumptionAtom, selectedDatetimeStringAtom } from 'utils/state/atoms';

import { useGetGeometries } from '../map-utils/getMapGrid';

// Helper function to calculate the centroid of a polygon
const getPolygonCentroid = (coordinates: number[][][]) => {
  let x = 0,
    y = 0,
    area = 0;
  const ring = coordinates[0]; // Use outer ring

  for (let index = 0; index < ring.length - 1; index++) {
    const xi = ring[index][0];
    const yi = ring[index][1];
    const xi1 = ring[index + 1][0];
    const yi1 = ring[index + 1][1];
    const a = xi * yi1 - xi1 * yi;
    area += a;
    x += (xi + xi1) * a;
    y += (yi + yi1) * a;
  }

  area *= 0.5;
  x /= 6 * area;
  y /= 6 * area;

  return [x, y];
};

function getWarningIconData(worldGeometries: MapGeometries, data: GridState | undefined) {
  if (!worldGeometries?.features || !data?.alerts) {
    return null;
  }

  const warningZones = data.alerts;
  const features = [];

  for (const zoneId of warningZones) {
    const zoneFeature = worldGeometries.features.find(
      (feature) => feature.properties?.zoneId === zoneId
    );

    if (zoneFeature?.geometry) {
      let centroid;

      if (zoneFeature.geometry.type === 'Polygon') {
        centroid = getPolygonCentroid(zoneFeature.geometry.coordinates);
      } else if (zoneFeature.geometry.type === 'MultiPolygon') {
        // Use the centroid of the largest polygon
        let largest = zoneFeature.geometry.coordinates[0];
        for (let index = 1; index < zoneFeature.geometry.coordinates.length; index++) {
          if (zoneFeature.geometry.coordinates[index][0].length > largest[0].length) {
            largest = zoneFeature.geometry.coordinates[index];
          }
        }
        centroid = getPolygonCentroid(largest);
      }

      if (centroid) {
        features.push({
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: centroid,
          },
          properties: {
            zoneId: zoneId,
          },
        });
      }
    }
  }

  return {
    type: 'FeatureCollection',
    features,
  };
}

export default function GridAlertsLayer() {
  const { worldGeometries } = useGetGeometries();
  const { data } = useGetState();

  const co2ColorScale = useCo2ColorScale();

  const warningIconData = useMemo(
    () => getWarningIconData(worldGeometries, data),
    [worldGeometries, data]
  );

  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const isConsumption = useAtomValue(isConsumptionAtom);

  return (
    <>
      {/* */}
      {warningIconData?.features.map((feature) => {
        const { zoneId } = feature.properties;
        const [longitude, latitude] = feature.geometry.coordinates;
        const zoneData = data?.datetimes[selectedDatetimeString]?.z[zoneId];
        const intensity = zoneData ? getCarbonIntensity(zoneData, isConsumption) : 0; // Default to 0 if no data
        const bgColor = co2ColorScale(intensity);
        const iconColor = getTextColor(bgColor);

        return (
          <Marker key={zoneId} longitude={longitude} latitude={latitude} anchor="center">
            <div className="flex items-center justify-center rounded-full bg-white/10 p-2">
              <FiAlertTriangle
                size={16}
                className={`-translate-y-px text-${iconColor}`}
              />
            </div>
          </Marker>
        );
      })}
    </>
  );
}
