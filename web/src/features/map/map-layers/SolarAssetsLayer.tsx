import useGetSolarAssets from 'api/getSolarAssets';
import { useAtomValue } from 'jotai';
import { Layer, Source } from 'react-map-gl/maplibre';
import { isSolarAssetsLayerEnabledAtom } from 'utils/state/atoms';

export default function SolarAssetsLayer() {
  const isSolarAssetsLayerEnabled = useAtomValue(isSolarAssetsLayerEnabledAtom);
  const { data: solarAssetsData } = useGetSolarAssets();

  const dataForSource = isSolarAssetsLayerEnabled
    ? solarAssetsData
    : { type: 'FeatureCollection', features: [] };

  // Log the first feature to help debug ID issues
  if (
    solarAssetsData &&
    typeof solarAssetsData === 'object' &&
    'features' in solarAssetsData &&
    Array.isArray(solarAssetsData.features) &&
    solarAssetsData.features.length > 0
  ) {
    const firstFeature = solarAssetsData.features[0];
    console.log('[SolarAssetsLayer] First feature:', {
      id: firstFeature.id,
      properties: firstFeature.properties,
      name: firstFeature.properties?.name,
    });
  }

  console.log('[SolarAssetsLayer] isSolarAssetsLayerEnabled:', isSolarAssetsLayerEnabled);
  console.log('[SolarAssetsLayer] solarAssetsData:', solarAssetsData);
  console.log('[SolarAssetsLayer] dataForSource:', dataForSource);

  return (
    <Source id="solar-assets" type="geojson" data={dataForSource} promoteId="name">
      {/* Main solar asset icon layer */}
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
          ] as any,
        }}
      />

      {/* Additional highlight layer for selected assets */}
      <Layer
        id="solar-assets-selected-highlight"
        type="circle"
        source="solar-assets"
        paint={{
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            4,
            10,
            6,
            15,
            8,
            20,
            10,
            25,
          ],
          'circle-color': '#ffbb00',
          'circle-opacity': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            0.3,
            0,
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffbb00',
          'circle-stroke-opacity': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            0.8,
            0,
          ],
        }}
      />
    </Source>
  );
}
