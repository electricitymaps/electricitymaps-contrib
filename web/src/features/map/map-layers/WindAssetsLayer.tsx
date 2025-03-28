import { useTheme } from 'hooks/theme';
import { Layer, Source } from 'react-map-gl/maplibre';

import { ZONE_SOURCE } from '../Map';

export default function WindAssetsLayer() {
  const data = {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        properties: {},
        geometry: {
          coordinates: [
            [
              [12.096_283_407_855_566, 55.686_690_037_726_24],
              [12.096_283_407_855_566, 55.683_746_218_327_684],
              [12.097_683_268_758_374, 55.683_746_218_327_684],
              [12.097_683_268_758_374, 55.686_690_037_726_24],
              [12.096_283_407_855_566, 55.686_690_037_726_24],
            ],
          ],
          type: 'Polygon',
        },
      },
    ],
  };

  const theme = useTheme();
  console.log('data', data);

  const stateLabelPaint = {
    'text-color': 'white',
    'text-halo-color': '#111827',
    'text-halo-width': 0.5,
    'text-halo-blur': 0.25,
    'text-opacity': 0.9,
  };

  return (
    <Source id="wind-assets" type="geojson" data={data}>
      <Layer
        id="wind-assets-box"
        type="symbol"
        source={ZONE_SOURCE}
        source-layer="zones-clickable-layer" // Specify the source layer
        layout={{
          'icon-image': 'wind-asset-box',
          'icon-size': 1.2,
          'icon-allow-overlap': true,
          'icon-overlap': 'always',
          'icon-ignore-placement': true,
        }}
        paint={{
          'icon-color': [
            'coalesce',
            ['feature-state', 'color'],
            ['get', 'color'],
            theme.clickableFill,
          ],
        }}
      />
      <Layer
        id="wind-assets-points"
        type="symbol"
        source="wind-assets"
        layout={{
          'icon-image': 'wind-asset-icon',
          'icon-size': 0.1,
          'icon-allow-overlap': true,
          'icon-overlap': 'always',
          'icon-ignore-placement': true, // Add this property
          'text-field': ['get', 'station_name'],
          'text-size': 10,
          'text-letter-spacing': 0.12,
          'text-transform': 'uppercase',
          'text-font': ['poppins-semibold'],
          'text-offset': [0, 3.5],
        }}
        paint={stateLabelPaint}
      />
    </Source>
  );
}
