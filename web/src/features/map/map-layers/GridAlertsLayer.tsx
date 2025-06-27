import useGetState from 'api/getState';
import { useMemo } from 'react';
import { Layer, Source } from 'react-map-gl/maplibre';

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

export default function GridAlertsLayer() {
  const { worldGeometries } = useGetGeometries();
  const dataState = useGetState();
  const dataState_ = dataState.data;
  console.log('State data:', dataState_);

  const warningIconData = useMemo(() => {
    if (!worldGeometries?.features) {
      return null;
    }

    // Create one point per unique zoneId that needs a warning
    const warningZones = dataState_.alerts; // Add more zone IDs as needed for example ['CA-ON', 'US-MIDA-PJM']
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
  }, [worldGeometries]);

  return (
    <>
      {/* Separate source for warning icons */}
      {warningIconData && (
        <Source id="warning-icons-source" type="geojson" data={warningIconData}>
          <Layer
            id="zones-warning-icon-layer"
            type="symbol"
            layout={{
              'icon-image': 'lucide-warning',
              'icon-size': 1.2,
              'icon-allow-overlap': true,
              'symbol-placement': 'point',
            }}
          />
        </Source>
      )}
    </>
  );
}
