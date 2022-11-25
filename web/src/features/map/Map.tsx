import mapboxgl from 'mapbox-gl';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { ReactElement, useEffect, useMemo, useRef, useState } from 'react';
import { Layer, Map, MapRef, NavigationControl, Source } from 'react-map-gl';
import { useCo2ColorScale, useTheme } from '../../hooks/theme';

import useGetState from 'api/getState';
import MapTooltip from 'components/MapTooltip';
import ExchangeLayer from 'features/exchanges/ExchangeLayer';
import { useAtom } from 'jotai';
import { useLocation, useNavigate } from 'react-router-dom';
import { getCO2IntensityByMode } from 'utils/helpers';
import { loadingMapAtom, selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state';
import CustomLayer from './map-utils/CustomLayer';
import { useGetGeometries } from './map-utils/getMapGrid';

const ZONE_SOURCE = 'zones-clickable';
const SOUTHERN_LATITUDE_BOUND = -66.947_193;
const NORTHERN_LATITUDE_BOUND = 84.313_245;
const MAP_STYLE = { version: 8, sources: {}, layers: [] };

type FeatureId = string | number | undefined;

interface Feature {
  featureId: FeatureId;
  zoneId: string;
}

// TODO: Selected feature-id should be stored in a global state instead (and as zoneId).
// We could even consider not changing it hear, but always reading it from the path parameter?
export default function MapPage(): ReactElement {
  const [hoveredFeature, setHoveredFeature] = useState<Feature>();
  const [selectedFeatureId, setSelectedFeatureId] = useState<FeatureId>();
  const [cursorType, setCursorType] = useState<string>('grab');
  const [timeAverage] = useAtom(timeAverageAtom);
  const [_, updateIsLoadingMap] = useAtom(loadingMapAtom);
  const [datetimeIndex] = useAtom(selectedDatetimeIndexAtom);
  const [isMoving, setIsMoving] = useState<boolean>(false);
  const [{ mousePositionX, mousePositionY }, setMousePosition] = useState({
    mousePositionX: 0,
    mousePositionY: 0,
  });
  const getCo2colorScale = useCo2ColorScale();
  const navigate = useNavigate();
  const location = useLocation();
  const createToWithState = (to: string) => `${to}${location.search}${location.hash}`;
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
      navigate(createToWithState(`/zone/${zoneId}`));
    } else {
      setSelectedFeatureId(undefined);
      navigate(createToWithState('/map'));
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
    if (hoveredFeature && (!feature || hoveredFeature.featureId !== feature.id)) {
      map.setFeatureState(
        { source: ZONE_SOURCE, id: hoveredFeature.featureId },
        { hover: false }
      );
    }
    if (feature && feature.id) {
      setCursorType('pointer');
      setHoveredFeature({ featureId: feature.id, zoneId: feature.properties?.zoneId });
      map.setFeatureState({ source: ZONE_SOURCE, id: feature.id }, { hover: true });

      setMousePosition({
        mousePositionX: event.point.x,
        mousePositionY: event.point.y,
      });
    } else {
      setCursorType('grab');
      setHoveredFeature(undefined);
    }
  };

  const onMouseOut = () => {
    const map = mapReference.current?.getMap();
    if (!map) {
      return;
    }

    if (hoveredFeature?.featureId !== null) {
      map.setFeatureState(
        { source: ZONE_SOURCE, id: hoveredFeature?.featureId },
        { hover: false }
      );
      setHoveredFeature(undefined);
    }
  };

  const onError = (event: mapboxgl.ErrorEvent) => {
    console.error(event.error);
    updateIsLoadingMap(false);
    // TODO: Show error message to user
    // TODO: Send to Sentry
    // TODO: Handle the "no webgl" error gracefully
  };

  const onLoad = () => {
    updateIsLoadingMap(false);
  };

  const onDragOrZoomStart = () => {
    setIsMoving(true);
  };

  const onDragOrZoomEnd = () => {
    setIsMoving(false);
  };

  return (
    <>
      {hoveredFeature && !isMoving && (
        <MapTooltip
          mousePositionX={mousePositionX}
          mousePositionY={mousePositionY}
          hoveredFeature={hoveredFeature}
        />
      )}
      <Map
        ref={mapReference}
        initialViewState={{
          // TODO: Make these dynamic depending on callerLocation from v6/state
          latitude: 37.8,
          longitude: -122.4,
          zoom: 2,
        }}
        interactiveLayerIds={['zones-clickable-layer', 'zones-hoverable-layer']}
        cursor={cursorType}
        onClick={onClick}
        onLoad={onLoad}
        onError={onError}
        onMouseMove={onMouseMove}
        onMouseOut={onMouseOut}
        onDragStart={onDragOrZoomStart}
        onZoomStart={onDragOrZoomStart}
        onZoomEnd={onDragOrZoomEnd}
        dragPan={{ maxSpeed: 0 }} // Disables easing effect to improve performance on exchange layer
        onDragEnd={onDragOrZoomEnd}
        minZoom={0.7}
        maxBounds={[
          [Number.NEGATIVE_INFINITY, SOUTHERN_LATITUDE_BOUND],
          [Number.POSITIVE_INFINITY, NORTHERN_LATITUDE_BOUND],
        ]}
        mapLib={maplibregl}
        style={{ minWidth: '100vw', height: '100vh' }}
        mapStyle={MAP_STYLE as mapboxgl.Style}
      >
        <Layer id="ocean" type="background" paint={styles.ocean} />
        <Source id="zones-clickable" generateId type="geojson" data={geometries}>
          <Layer id="zones-clickable-layer" type="fill" paint={styles.zonesClickable} />
          <Layer id="zones-hoverable-layer" type="fill" paint={styles.zonesHover} />
          <Layer id="zones-border" type="line" paint={styles.zonesBorder} />
        </Source>
        {/* TODO: Get rid of the inline styling here if/when possible */}
        <NavigationControl
          style={{
            marginRight: 12,
            marginTop: 98,
            width: '33px',
            boxShadow: '0px 1px 1px  rgb(0 0 0 / 0.1)',
            border: 0,
            color: 'white',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
          showCompass={false}
        ></NavigationControl>
        <CustomLayer>
          <ExchangeLayer isMoving={isMoving} />
        </CustomLayer>
      </Map>
    </>
  );
}
