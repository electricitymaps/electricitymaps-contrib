import useGetChargingStations from 'api/getChargingStations';
import { useTheme } from 'hooks/theme';
import { Layer, Source } from 'react-map-gl/maplibre';

import { ZONE_SOURCE } from '../Map';
import { useGetGeometries } from '../map-utils/getMapGrid';

export default function ChargingStationsLayer() {
  const { data } = useGetChargingStations();
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
    <Source id="charging-stations" type="geojson" data={data}>
      <Layer
        id="charging-stations-box"
        type="symbol"
        source={ZONE_SOURCE}
        source-layer="zones-clickable-layer" // Specify the source layer
        layout={{
          'icon-image': 'charging-station-box',
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
        id="charging-stations-points"
        type="symbol"
        source="charging-stations"
        layout={{
          'icon-image': 'charging-station-icon',
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
