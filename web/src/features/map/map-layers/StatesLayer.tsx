import { useTheme } from 'hooks/theme';
import { Layer, Source } from 'react-map-gl';

import { useGetGeometries } from '../map-utils/getMapGrid';

export default function StatesLayer() {
  const { statesGeometries } = useGetGeometries();
  const theme = useTheme();

  const statesBorderStyle = {
    'line-color': theme.stateBorderColor,
    'line-width': 1.4,
    'line-dasharray': [1, 1],
    'line-opacity': ['interpolate', ['linear'], ['zoom'], 2.8, 0, 3, 0.9],
  } as mapboxgl.LinePaint;

  const stateLabelLayout = {
    'symbol-placement': 'point',
    'text-size': 12,
    'text-letter-spacing': 0.12,
    'text-transform': 'uppercase',
    'text-font': ['poppins-semibold'],
  } as mapboxgl.SymbolLayout;

  const stateLabelPaint = {
    'text-color': 'white',
    'text-halo-color': '#111827',
    'text-halo-width': 0.5,
    'text-halo-blur': 0.25,
    'text-opacity': 0.9,
  } as mapboxgl.SymbolPaint;

  return (
    <Source id="states" type="geojson" data={statesGeometries}>
      <Layer
        id="states-border"
        beforeId="zones-selectable-layer"
        type="line"
        paint={statesBorderStyle}
        source="states"
      />
      <Layer
        id="state-labels-name"
        type="symbol"
        source="states"
        layout={{
          'text-field': ['get', 'stateName'],
          ...stateLabelLayout,
        }}
        paint={stateLabelPaint}
        minzoom={4.5}
      />
      <Layer
        id="state-labels-id"
        type="symbol"
        source="states"
        layout={{
          'text-field': ['get', 'stateId'],
          ...stateLabelLayout,
        }}
        paint={stateLabelPaint}
        maxzoom={4.5}
        minzoom={2.9}
      />
    </Source>
  );
}
