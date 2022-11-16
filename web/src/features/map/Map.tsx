import Head from 'components/Head';
import LoadingOrError from 'components/LoadingOrError';
import mapboxgl from 'mapbox-gl';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { ReactElement, useEffect, useMemo, useRef, useState } from 'react';
import { Layer, Map, MapRef, Source } from 'react-map-gl';
import { useCo2ColorScale, useTheme } from '../../hooks/theme';

import useGetState from 'api/getState';
import { useAtom } from 'jotai';
import { useNavigate } from 'react-router-dom';
import { getCO2IntensityByMode } from 'utils/helpers';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state';
import { useGetGeometries } from './map-utils/getMapGrid';

const ZONE_SOURCE = 'zones-clickable';

const mapStyle = { version: 8, sources: {}, layers: [] };

export default function MapPage(): ReactElement {
  const [hoveredFeatureId, setHoveredFeatureId] = useState<string | number | undefined>();
  const [selectedFeatureId, setSelectedFeatureId] = useState<
    string | number | undefined
  >();
  const [cursorType, setCursorType] = useState<string>('grab');
  const [timeAverage] = useAtom(timeAverageAtom);
  const [datetimeIndex] = useAtom(selectedDatetimeIndexAtom);
  const getCo2colorScale = useCo2ColorScale();
  const navigate = useNavigate();

  const theme = useTheme();
  // Calculate layer styles only when the theme changes
  // To keep the stable and prevent excessive rerendering.
  const styles = useMemo(
    () => ({
      ocean: { 'background-color': theme.oceanColor },
      zonesBorder: {
        'line-color': [
          'case',
          ['boolean', ['feature-state', 'selected'], false],
          'white',
          theme.strokeColor,
        ],
        // Note: if stroke width is 1px, then it is faster to use fill-outline in fill layer
        'line-width': [
          'case',
          ['boolean', ['feature-state', 'selected'], false],
          (theme.strokeWidth as number) * 10,
          theme.strokeWidth,
        ],
      } as mapboxgl.LinePaint,
      zonesClickable: {
        'fill-color': [
          'coalesce',
          ['feature-state', 'color'],
          ['get', 'color'],
          theme.clickableFill,
        ],
      } as mapboxgl.FillPaint,
      zonesHover: {
        'fill-color': '#FFFFFF',
        'fill-opacity': ['case', ['boolean', ['feature-state', 'hover'], false], 0.3, 0],
      } as mapboxgl.FillPaint,
    }),
    [theme]
  );

  const { isLoading, isError, error, data } = useGetState(timeAverage);
  const mapReference = useRef<MapRef>(null);
  const geometries = useGetGeometries();

  useEffect(() => {
    // This effect colors the zones based on the co2 intensity
    const map = mapReference.current?.getMap();

    if (!map || isLoading || isError) {
      return;
    }

    // An issue where the map has not loaded source yet causing map errors
    const isSourceLoaded = map.getSource('zones-clickable') != undefined;
    if (!isSourceLoaded) {
      return;
    }

    for (const [index, feature] of geometries.features.entries()) {
      const { zoneId } = feature.properties;
      const zone = data.data?.zones[zoneId];

      const co2intensity =
        zone && zone[datetimeIndex]
          ? getCO2IntensityByMode(zone[datetimeIndex], 'consumption')
          : undefined;

      const fillColor = co2intensity
        ? getCo2colorScale(co2intensity)
        : theme.clickableFill;

      const existingColor = map.getFeatureState({
        source: 'zones-clickable',
        id: index,
      })?.color;

      if (existingColor !== fillColor) {
        map.setFeatureState(
          {
            source: 'zones-clickable',
            id: index,
          },
          {
            color: fillColor,
          }
        );
      }
    }
  }, [mapReference, geometries, data, getCo2colorScale, datetimeIndex]);

  const onClick = (event: mapboxgl.MapLayerMouseEvent) => {
    const map = mapReference.current?.getMap();
    if (!map || !event.features) {
      return;
    }
    const feature = event.features[0];

    // Remove state from old feature if we are no longer hovering anything,
    // or if we are hovering a different feature than the previous one
    if (selectedFeatureId && (!feature || selectedFeatureId !== feature.id)) {
      map.setFeatureState(
        { source: ZONE_SOURCE, id: selectedFeatureId },
        { selected: false }
      );
    }

    if (feature && feature.properties) {
      setSelectedFeatureId(feature.id);
      map.setFeatureState({ source: ZONE_SOURCE, id: feature.id }, { selected: true });

      const zoneId = feature.properties.zoneId;
      // TODO: Open left panel
      // TODO: Consider using flyTo zone?
      navigate(`/zone/${zoneId}`);
    } else {
      setSelectedFeatureId(undefined);
      navigate('/map');
    }
  };

  // TODO: Consider if we need to ignore zone hovering if the map is dragging
  // TODO: Save cursor position to be used for tooltip
  const onMouseMove = (event: mapboxgl.MapLayerMouseEvent) => {
    const map = mapReference.current?.getMap();
    if (!map || !event.features) {
      return;
    }

    const feature = event.features[0];

    // Remove state from old feature if we are no longer hovering anything,
    // or if we are hovering a different feature than the previous one
    if (hoveredFeatureId && (!feature || hoveredFeatureId !== feature.id)) {
      map.setFeatureState(
        { source: ZONE_SOURCE, id: hoveredFeatureId },
        { hover: false }
      );
    }

    if (feature && feature.id) {
      setCursorType('pointer');
      setHoveredFeatureId(feature.id);
      map.setFeatureState({ source: ZONE_SOURCE, id: feature.id }, { hover: true });
    } else {
      setCursorType('grab');
      setHoveredFeatureId(undefined);
    }
  };

  const onMouseOut = () => {
    const map = mapReference.current?.getMap();
    if (!map) {
      return;
    }

    if (hoveredFeatureId !== null) {
      map.setFeatureState(
        { source: ZONE_SOURCE, id: hoveredFeatureId },
        { hover: false }
      );
      setHoveredFeatureId(undefined);
    }
  };

  const southernLatitudeBound = -62.947_193;
  const northernLatitudeBound = 84.613_245;

  const onError = (event: mapboxgl.ErrorEvent) => {
    console.error(event.error);
    // TODO: Remove loading overlay
    // TODO: Show error message to user
  };
  return (
    <>
      <Head title="Electricity Maps" />
      <Map
        ref={mapReference}
        initialViewState={{
          latitude: 37.8,
          longitude: -122.4,
          zoom: 2,
        }}
        interactiveLayerIds={['zones-clickable-layer', 'zones-hoverable-layer']}
        cursor={cursorType}
        onClick={onClick}
        onError={onError}
        onMouseMove={onMouseMove}
        onMouseOut={onMouseOut}
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
        <Source id="zones-clickable" generateId type="geojson" data={geometries}>
          <Layer id="zones-clickable-layer" type="fill" paint={styles.zonesClickable} />
          <Layer id="zones-hoverable-layer" type="fill" paint={styles.zonesHover} />
          <Layer id="zones-border" type="line" paint={styles.zonesBorder} />
        </Source>
      </Map>
    </>
  );
}
