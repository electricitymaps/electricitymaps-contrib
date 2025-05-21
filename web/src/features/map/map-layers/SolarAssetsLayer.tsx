import useGetSolarAssets from 'api/getSolarAssets';
import { useAtomValue } from 'jotai';
import { Layer, Source } from 'react-map-gl/maplibre';
import { isRenewablesLayerEnabledAtom } from 'utils/state/atoms';

export default function SolarAssetsLayer() {
  const isRenewablesLayerEnabled = useAtomValue(isRenewablesLayerEnabledAtom);
  const { data: solarAssetsData } = useGetSolarAssets();

  const dataForSource = isRenewablesLayerEnabled
    ? solarAssetsData
    : { type: 'FeatureCollection', features: [] };

  console.log('[SolarAssetsLayer] isRenewablesLayerEnabled:', isRenewablesLayerEnabled);
  console.log('[SolarAssetsLayer] solarAssetsData:', solarAssetsData);
  console.log('[SolarAssetsLayer] dataForSource:', dataForSource);

  const stateLabelPaint = {
    'text-color': 'red',
    'text-halo-color': '#111827',
    'text-halo-width': 0.5,
    'text-halo-blur': 0.25,
    'text-opacity': 0.9,
  };
  return (
    <Source id="solar-assets" type="geojson" data={dataForSource} promoteId="name">
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
        paint={{
          ...stateLabelPaint,
          'icon-opacity': [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            0.7,
            1,
          ],
          'icon-color': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            '#007bff',
            stateLabelPaint['text-color'],
          ],
        }}
      />
    </Source>
  );
}
