import Head from 'components/Head';
import LoadingOrError from 'components/LoadingOrError';
import { ReactElement, useMemo } from 'react';
import useGetState from 'api/getState';
import { Map, Source, Layer } from 'react-map-gl';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useCo2ColorScale, useTheme } from '../../hooks/theme';
import { FillPaint } from 'mapbox-gl';

import { TimeAverages } from 'utils/constants';

const mapStyle = { version: 8, sources: {}, layers: [] };

export default function MapPage(): ReactElement {
  const theme = useTheme();
  const getCo2colorScale = useCo2ColorScale();
  // Calculate layer styles only when the theme changes
  // To keep the stable and prevent excessive rerendering.
  const styles = useMemo(
    () => ({
      hover: { 'fill-color': 'white', 'fill-opacity': 0.3 },
      ocean: { 'background-color': theme.oceanColor },
      zonesBorder: { 'line-color': theme.strokeColor, 'line-width': theme.strokeWidth },
      zonesClickable: {
        'fill-color': ['coalesce', ['feature-state', 'color'], ['get', 'color'], theme.clickableFill],
      } as FillPaint,
    }),
    [theme]
  );

  const { isLoading, isError, error, data } = useGetState(TimeAverages.HOURLY, getCo2colorScale);

  if (isLoading || isError) {
    return <LoadingOrError error={error as Error} />;
  }

  const zonesClickable = data;
  const southernLatitudeBound = -62.947_193;
  const northernLatitudeBound = 84.613_245;

  return (
    <>
      <Head title="Electricity Maps" />
      <Map
        initialViewState={{
          latitude: 37.8,
          longitude: -122.4,
          zoom: 2,
        }}
        minZoom={0.7}
        maxBounds={[
          [Number.NEGATIVE_INFINITY, southernLatitudeBound],
          [Number.POSITIVE_INFINITY, northernLatitudeBound],
        ]}
        mapLib={maplibregl}
        style={{ minWidth: '100vw', height: '100vh' }}
        mapStyle={mapStyle as mapboxgl.Style}
      >
        <Layer id="ocean" type="background" paint={styles.ocean} />
        <Source id="zones-clickable" generateId type="geojson" data={data}>
          <Layer id="zones-clickable-layer" type="fill" paint={styles.zonesClickable} />
          <Layer id="zones-border" type="line" paint={styles.zonesBorder} />
          {/* Note: if stroke width is 1px, then it is faster to use fill-outline in fill layer */}
        </Source>
        <Source type="geojson" data={zonesClickable}>
          <Layer id="hover" type="fill" paint={styles.hover} filter={['hoverFilter //TODO']} />
        </Source>
      </Map>

    </>
  );
}
