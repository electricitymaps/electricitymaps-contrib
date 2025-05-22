import useGetSolarAssets from 'api/getSolarAssets';
import { useTheme } from 'hooks/theme';
import { useAtomValue, useSetAtom } from 'jotai';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';
import useResizeObserver from 'use-resize-observer';
import {
  isRenewablesLayerEnabledAtom,
  renewablesLayerLoadingAtom,
} from 'utils/state/atoms';

import { ZONE_SOURCE } from '../Map';

export default function SolarAssetsLayer() {
  const setIsLoadingRenewablesLayer = useSetAtom(renewablesLayerLoadingAtom);
  const isRenewablesLayerEnabled = useAtomValue(isRenewablesLayerEnabledAtom);
  const { data: solarAssetsData } = useGetSolarAssets();

  const { current: mapReference } = useMap();
  const { ref } = useResizeObserver<HTMLDivElement>();
  const theme = useTheme();

  if (!mapReference || !isRenewablesLayerEnabled) {
    return <div ref={ref} className="h-full w-full" />;
  }

  const stateLabelPaint = {
    'text-color': 'red',
    'text-halo-color': '#111827',
    'text-halo-width': 0.5,
    'text-halo-blur': 0.25,
    'text-opacity': 0.9,
  };
  setIsLoadingRenewablesLayer(false);
  return (
    <Source
      id="solar-assets"
      type="geojson"
      data={
        'https://storage.googleapis.com/testing-gzipped-geojson/solar_assets.min.geojson.gz'
      }
    >
      <Layer
        id="solar-assets-box"
        type="symbol"
        source={ZONE_SOURCE}
        source-layer="zones-clickable-layer" // Specify the source layer
        layout={{
          'icon-image': 'solar-asset-box',
          'icon-size': 10,
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
