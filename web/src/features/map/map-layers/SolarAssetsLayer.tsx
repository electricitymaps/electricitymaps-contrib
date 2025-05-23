import useGetSolarAssets from 'api/getSolarAssets';
import { MIN_ZOOM_FOR_ASSET_SYMBOL_APPEARING } from 'features/assets/utils';
import { useAtomValue, useSetAtom } from 'jotai';
import { Layer, Source } from 'react-map-gl/maplibre';
import useResizeObserver from 'use-resize-observer';
import {
  isSolarAssetsLayerEnabledAtom,
  solarAssetsLayerLoadingAtom,
} from 'utils/state/atoms';

export default function SolarAssetsLayer() {
  const setIsLoadingSolarLayer = useSetAtom(solarAssetsLayerLoadingAtom);
  const isSolarAssetsLayerEnabled = useAtomValue(isSolarAssetsLayerEnabledAtom);
  const { data: solarAssetsData } = useGetSolarAssets();
  const { ref } = useResizeObserver<HTMLDivElement>();

  if (!isSolarAssetsLayerEnabled) {
    return <div ref={ref} className="h-full w-full" />;
  }

  setIsLoadingSolarLayer(false);

  return (
    <Source id="solar-assets" type="geojson" data={solarAssetsData} promoteId="name">
      <Layer
        id="solar-assets-points"
        type="symbol"
        source="solar-assets"
        layout={{
          'icon-image': 'solar-asset-icon',
          'icon-size': [
            'interpolate',
            ['linear'],
            ['zoom'],
            MIN_ZOOM_FOR_ASSET_SYMBOL_APPEARING,
            0,
            6,
            0.3,
            8,
            0.8,
          ],
          'icon-allow-overlap': true,
          'icon-overlap': 'always',
          'icon-ignore-placement': true,
        }}
        paint={{
          'icon-opacity': [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            0.7,
            1,
          ],
          'icon-color': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            '#ffbb00',
            '#ff4400',
          ] as [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            string,
            string
          ],
        }}
      />
    </Source>
  );
}
