import 'maplibre-gl/dist/maplibre-gl.css';

import useGetState from 'api/getState';
import ExchangeLayer from 'features/exchanges/ExchangeLayer';
import ZoomControls from 'features/map-controls/ZoomControls';
import { leftPanelOpenAtom } from 'features/panels/panelAtoms';
import SolarLayer from 'features/weather-layers/solar/SolarLayer';
import WindLayer from 'features/weather-layers/wind-layer/WindLayer';
import { useAtom, useSetAtom } from 'jotai';
import mapboxgl from 'mapbox-gl';
import maplibregl from 'maplibre-gl';
import { ReactElement, useEffect, useRef, useState } from 'react';
import { Map, MapRef } from 'react-map-gl';
import { matchPath, useLocation, useNavigate } from 'react-router-dom';
import { Mode } from 'utils/constants';
import { createToWithState, getCO2IntensityByMode } from 'utils/helpers';
import {
  productionConsumptionAtom,
  selectedDatetimeIndexAtom,
  spatialAggregateAtom,
} from 'utils/state/atoms';

import { useCo2ColorScale, useTheme } from '../../hooks/theme';
import BackgroundLayer from './map-layers/BackgroundLayer';
import StatesLayer from './map-layers/StatesLayer';
import ZonesLayer from './map-layers/ZonesLayer';
import CustomLayer from './map-utils/CustomLayer';
import { useGetGeometries } from './map-utils/getMapGrid';
import {
  hoveredZoneAtom,
  loadingMapAtom,
  mapMovingAtom,
  mousePositionAtom,
} from './mapAtoms';
import { FeatureId } from './mapTypes';

export const ZONE_SOURCE = 'zones-clickable';
const SOUTHERN_LATITUDE_BOUND = -78;
const NORTHERN_LATITUDE_BOUND = 85;
const MAP_STYLE = {
  version: 8,
  sources: {},
  layers: [],
  glyphs: 'fonts/{fontstack}/{range}.pbf',
};
const isMobile = window.innerWidth < 768;

type MapPageProps = {
  onMapLoad?: (map: mapboxgl.Map) => void;
};

// TODO: Selected feature-id should be stored in a global state instead (and as zoneId).
// We could even consider not changing it hear, but always reading it from the path parameter?
export default function MapPage({ onMapLoad }: MapPageProps): ReactElement {
  const setIsMoving = useSetAtom(mapMovingAtom);
  const setMousePosition = useSetAtom(mousePositionAtom);
  const [isLoadingMap, setIsLoadingMap] = useAtom(loadingMapAtom);
  const [hoveredZone, setHoveredZone] = useAtom(hoveredZoneAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const setLeftPanelOpen = useSetAtom(leftPanelOpenAtom);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const location = useLocation();
  const getCo2colorScale = useCo2ColorScale();
  const navigate = useNavigate();
  const theme = useTheme();
  const [currentMode] = useAtom(productionConsumptionAtom);
  const mixMode = currentMode === Mode.CONSUMPTION ? 'consumption' : 'production';
  const [selectedZoneId, setSelectedZoneId] = useState<FeatureId>();
  const [isDragging, setIsDragging] = useState(false);
  const [isZooming, setIsZooming] = useState(false);
  const [spatialAggregate] = useAtom(spatialAggregateAtom);
  // Calculate layer styles only when the theme changes
  // To keep the stable and prevent excessive rerendering.
  const { isLoading, isSuccess, isError, data } = useGetState();
  const { worldGeometries } = useGetGeometries();
  const mapReference = useRef<MapRef>(null);
  const map = mapReference.current?.getMap();

  useEffect(() => {
    // This effect colors the zones based on the co2 intensity
    if (!map || isLoading || isError) {
      return;
    }
    map?.touchZoomRotate.disableRotation();
    map?.touchPitch.disable();
    const isSourceLoaded =
      map &&
      map.getSource(ZONE_SOURCE) !== undefined &&
      map.getSource('states') !== undefined &&
      map.isSourceLoaded('states');

    if (!isSourceLoaded || isLoadingMap) {
      return;
    }
    for (const feature of worldGeometries.features) {
      const { zoneId } = feature.properties;
      const zone = data.data?.zones[zoneId];
      const co2intensity =
        zone && zone[selectedDatetime.datetimeString]
          ? getCO2IntensityByMode(zone[selectedDatetime.datetimeString], mixMode)
          : undefined;
      const fillColor = co2intensity
        ? getCo2colorScale(co2intensity)
        : theme.clickableFill;
      const existingColor = map.getFeatureState({
        source: ZONE_SOURCE,
        id: zoneId,
      })?.color;

      if (existingColor !== fillColor) {
        map.setFeatureState(
          {
            source: ZONE_SOURCE,
            id: zoneId,
          },
          {
            color: fillColor,
          }
        );
      }
    }
  }, [
    data,
    getCo2colorScale,
    selectedDatetime,
    mixMode,
    isLoadingMap,
    spatialAggregate,
    isSuccess,
  ]);

  useEffect(() => {
    // Run on first load to center the map on the user's location
    if (!map || isError || !isFirstLoad) {
      return;
    }
    if (data?.callerLocation && !selectedZoneId) {
      map.flyTo({ center: [data.callerLocation[0], data.callerLocation[1]] });
      setIsFirstLoad(false);
    }
  }, [isSuccess]);

  useEffect(() => {
    // Run when the selected zone changes
    // deselect and dehover zone when navigating to /map (e.g. using back button on mobile panel)
    if (map && location.pathname === '/map' && selectedZoneId) {
      map.setFeatureState(
        { source: ZONE_SOURCE, id: selectedZoneId },
        { selected: false, hover: false }
      );
      setHoveredZone(null);
    }
    // Center the map on the selected zone
    const zoneId = matchPath('/zone/:zoneId', location.pathname)?.params.zoneId;
    setSelectedZoneId(zoneId);
    if (map && zoneId) {
      const feature = worldGeometries.features.find(
        (feature) => feature.properties.zoneId === zoneId
      );
      // if no feature matches, it means that the selected zone is not in current spatial resolution.
      // We cannot include geometries in dependencies, as we don't want to flyTo when user switches
      // between spatial resolutions. Therefore we find an approximate feature based on the zoneId.
      if (!feature) {
        return;
      }

      const center = feature.properties.center;
      map.setFeatureState({ source: ZONE_SOURCE, id: zoneId }, { selected: true });
      setLeftPanelOpen(true);
      const centerMinusLeftPanelWidth = [center[0] - 10, center[1]] as [number, number];
      map.flyTo({ center: isMobile ? center : centerMinusLeftPanelWidth, zoom: 3.5 });
    }
  }, [location.pathname, isLoadingMap]);

  const onClick = (event: mapboxgl.MapLayerMouseEvent) => {
    if (!map || !event.features) {
      return;
    }
    const feature = event.features[0];

    // Remove state from old feature if we are no longer hovering anything,
    // or if we are hovering a different feature than the previous one
    if (selectedZoneId && (!feature || selectedZoneId !== feature.id)) {
      map.setFeatureState(
        { source: ZONE_SOURCE, id: selectedZoneId },
        { selected: false }
      );
    }

    if (hoveredZone && (!feature || hoveredZone.featureId !== selectedZoneId)) {
      map.setFeatureState(
        { source: ZONE_SOURCE, id: hoveredZone.featureId },
        { hover: false }
      );
    }
    setHoveredZone(null);
    if (feature && feature.properties) {
      const zoneId = feature.properties.zoneId;
      navigate(createToWithState(`/zone/${zoneId}`));
    } else {
      navigate(createToWithState('/map'));
    }
  };

  // TODO: Consider if we need to ignore zone hovering if the map is dragging
  const onMouseMove = (event: mapboxgl.MapLayerMouseEvent) => {
    if (!map || !event.features) {
      return;
    }
    const feature = event.features[0];
    const isHoveringAZone = feature?.id !== undefined;
    const isHoveringANewZone = isHoveringAZone && hoveredZone?.featureId !== feature?.id;

    // Reset currently hovered zone if we are no longer hovering anything
    if (!isHoveringAZone && hoveredZone) {
      setHoveredZone(null);
      map.setFeatureState(
        { source: ZONE_SOURCE, id: hoveredZone?.featureId },
        { hover: false }
      );
    }

    // Do no more if we are not hovering a zone
    if (!isHoveringAZone) {
      return;
    }

    // Update mouse position to help position the tooltip
    setMousePosition({
      x: event.point.x,
      y: event.point.y,
    });

    // Update hovered zone if we are hovering a new zone
    if (isHoveringANewZone) {
      // Reset the old one first
      if (hoveredZone) {
        map.setFeatureState(
          { source: ZONE_SOURCE, id: hoveredZone?.featureId },
          { hover: false }
        );
      }

      setHoveredZone({ featureId: feature.id, zoneId: feature.properties?.zoneId });
      map.setFeatureState({ source: ZONE_SOURCE, id: feature.id }, { hover: true });
    }
  };

  const onMouseOut = () => {
    if (!map) {
      return;
    }

    // Reset hovered state when mouse leaves map (e.g. cursor moving into panel)
    if (hoveredZone?.featureId !== undefined) {
      map.setFeatureState(
        { source: ZONE_SOURCE, id: hoveredZone?.featureId },
        { hover: false }
      );
      setHoveredZone(null);
    }
  };

  const onError = (event: mapboxgl.ErrorEvent) => {
    console.error(event.error);
    setIsLoadingMap(false);
    // TODO: Show error message to user
    // TODO: Send to Sentry
    // TODO: Handle the "no webgl" error gracefully
  };

  const onLoad = () => {
    setIsLoadingMap(false);
    if (onMapLoad && mapReference.current) {
      onMapLoad(mapReference.current.getMap());
    }
  };

  const onZoomStart = () => {
    setIsZooming(true);
    setIsMoving(true);
  };
  const onDragStart = () => {
    setIsDragging(true);
    setIsMoving(true);
  };

  const onZoomEnd = () => {
    setIsZooming(false);
    if (!isDragging) {
      setIsMoving(false);
    }
  };
  const onDragEnd = () => {
    setIsDragging(false);
    if (!isZooming) {
      setIsMoving(false);
    }
  };

  return (
    <Map
      ref={mapReference}
      initialViewState={{
        latitude: 50.905,
        longitude: 6.528,
        zoom: 2.5,
      }}
      interactiveLayerIds={['zones-clickable-layer', 'zones-hoverable-layer']}
      cursor={hoveredZone ? 'pointer' : 'grab'}
      onClick={onClick}
      onLoad={onLoad}
      onError={onError}
      onMouseMove={onMouseMove}
      onMouseOut={onMouseOut}
      onTouchStart={onDragStart}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onZoomStart={onZoomStart}
      onZoomEnd={onZoomEnd}
      dragPan={{ maxSpeed: 0 }} // Disables easing effect to improve performance on exchange layer
      dragRotate={false}
      minZoom={0.7}
      maxBounds={[
        [Number.NEGATIVE_INFINITY, SOUTHERN_LATITUDE_BOUND],
        [Number.POSITIVE_INFINITY, NORTHERN_LATITUDE_BOUND],
      ]}
      mapLib={maplibregl}
      style={{ minWidth: '100vw', height: '100vh' }}
      mapStyle={MAP_STYLE as mapboxgl.Style}
    >
      <BackgroundLayer />
      <ZonesLayer />
      <StatesLayer />
      <CustomLayer>
        <WindLayer />
      </CustomLayer>
      <CustomLayer>
        <ExchangeLayer />
      </CustomLayer>
      <CustomLayer>
        <SolarLayer />
      </CustomLayer>
      <ZoomControls />
    </Map>
  );
}
