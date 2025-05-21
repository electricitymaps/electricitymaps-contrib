import useGetSolarAssets from 'api/getSolarAssets';
import { useTheme } from 'hooks/theme';
import { Layer, Source } from 'react-map-gl/maplibre';

import { ZONE_SOURCE } from '../Map';

export default function SolarAssetsLayer() {
  const { data } = useGetSolarAssets();
  const theme = useTheme();

  const stateLabelPaint = {
    'text-color': 'white',
    'text-halo-color': '#111827',
    'text-halo-width': 0.5,
    'text-halo-blur': 0.25,
    'text-opacity': 0.9,
  };

  return (
    <Source id="solar-assets" type="geojson" data={data}>
      <Layer
        id="solar-assets-box"
        type="symbol"
        source={ZONE_SOURCE}
        source-layer="zones-clickable-layer" // Specify the source layer
        layout={{
          'icon-image': 'solar-asset-box',
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
        id="solar-assets-points"
        type="symbol"
        source="solar-assets"
        layout={{
          'icon-image': 'solar-asset-icon',
          'icon-size': ['interpolate', ['linear'], ['zoom'], 4, 0, 6, 0.3, 8, 0.8],
          'icon-allow-overlap': true,
          'icon-overlap': 'always',
          'icon-ignore-placement': true,
        }}
        paint={stateLabelPaint}
      />
    </Source>
  );
}
