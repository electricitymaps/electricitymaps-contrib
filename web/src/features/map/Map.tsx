import { App } from '@capacitor/app';
import { PluginListenerHandle } from '@capacitor/core/types/definitions';
import useGetState from 'api/getState';
import { SIDEBAR_WIDTH } from 'features/app-sidebar/AppSidebar';
import ExchangeLayer from 'features/exchanges/ExchangeLayer';
import ZoomControls from 'features/map-controls/ZoomControls';
import { leftPanelOpenAtom } from 'features/panels/panelAtoms';
import SolarLayer from 'features/weather-layers/solar/SolarLayer';
import WindLayer from 'features/weather-layers/wind-layer/WindLayer';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';
import { StyleSpecification } from 'maplibre-gl';
import { ReactElement, useCallback, useEffect, useState } from 'react';
import { ErrorEvent, Map, MapRef } from 'react-map-gl/maplibre';
import { useLocation, useParams } from 'react-router-dom';
import { RouteParameters } from 'types';
import {
  getCarbonIntensity,
  useNavigateWithParameters,
  useUserLocation,
} from 'utils/helpers';
import {
  isConsumptionAtom,
  selectedDatetimeStringAtom,
  spatialAggregateAtom,
  userLocationAtom,
} from 'utils/state/atoms';

import { useCo2ColorScale, useTheme } from '../../hooks/theme';
import BackgroundLayer from './map-layers/BackgroundLayer';
import SolarAssetsLayer from './map-layers/SolarAssetsLayer';
import StatesLayer from './map-layers/StatesLayer';
import ZonesLayer from './map-layers/ZonesLayer';
import CustomLayer from './map-utils/CustomLayer';
import { useGetGeometries } from './map-utils/getMapGrid';
import { getZoneIdFromLocation } from './map-utils/getZoneIdFromLocation';
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
  onMapLoad?: (map: maplibregl.Map) => void;
};

interface ExtendedWindow extends Window {
  killMap?: () => void;
}

// TODO: Selected feature-id should be stored in a global state instead (and as zoneId).
// We could even consider not changing it hear, but always reading it from the path parameter?
export default function MapPage({ onMapLoad }: MapPageProps): ReactElement {
  const setIsMoving = useSetAtom(mapMovingAtom);
  const setMousePosition = useSetAtom(mousePositionAtom);
  const [isLoadingMap, setIsLoadingMap] = useAtom(loadingMapAtom);
  const [hoveredZone, setHoveredZone] = useAtom(hoveredZoneAtom);
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const setLeftPanelOpen = useSetAtom(leftPanelOpenAtom);
  const setUserLocation = useSetAtom(userLocationAtom);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const [isSourceLoaded, setSourceLoaded] = useState(false);
  const location = useLocation();
  const getCo2colorScale = useCo2ColorScale();
  const navigate = useNavigateWithParameters();
  const theme = useTheme();
  const isConsumption = useAtomValue(isConsumptionAtom);
  const [selectedZoneId, setSelectedZoneId] = useState<FeatureId>();
  const spatialAggregate = useAtomValue(spatialAggregateAtom);
  // Calculate layer styles only when the theme changes
  // To keep the stable and prevent excessive rerendering.
  const { isLoading, isSuccess, isError, data } = useGetState();
  const { worldGeometries } = useGetGeometries();
  const [mapReference, setMapReference] = useState<MapRef | null>(null);
  const map = mapReference?.getMap();
  const userLocation = useUserLocation();
  const { zoneId: pathZoneId } = useParams<RouteParameters>();
  const [wasInBackground, setWasInBackground] = useState(false);
  const onMapReferenceChange = useCallback((reference: MapRef) => {
    setMapReference(reference);
  }, []);

  useEffect(() => {
    let subscription: PluginListenerHandle | null = null;
    // Dev testing function to break the map state and test recovery
    if (import.meta.env.DEV) {
      (window as ExtendedWindow).killMap = () => {
        console.log('Attempting to break map state');
        if (map && map.loaded()) {
          try {
            if (map.getSource(ZONE_SOURCE)) {
              console.log('Removing zone source');
              map.removeSource(ZONE_SOURCE);
            }

            const canvas = map.getCanvas();
            canvas.width = 0;
            canvas.height = 0;

            const container = map.getContainer();
            container.innerHTML = '';

            console.log('Map should now be broken');
          } catch (error) {
            console.error('Error while killing map:', error);
          }
        } else {
          console.log('Map not ready or already broken');
        }
      };
    }
    const setupListener = async () => {
      subscription = await App.addListener('appStateChange', ({ isActive }) => {
        if (!isActive) {
          setWasInBackground(true);
        } else if (wasInBackground && map) {
          const isMapBroken =
            !map.loaded() ||
            map.getCanvas().width === 0 ||
            map.getContainer().offsetWidth === 0 ||
            map.getContainer().style.display === 'none';
          if (isMapBroken) {
            window.location.reload();
          } else {
            map.resize();
          }
        }
      });
    };

    setupListener();

    return () => {
      if (subscription) {
        subscription.remove();
      }
    };
  }, [map, wasInBackground, setMapReference]);

  useEffect(() => {
    const setSourceLoadedForMap = () => {
      setSourceLoaded(
        Boolean(
          map?.getSource(ZONE_SOURCE) !== undefined &&
            map?.getSource('states') !== undefined &&
            map?.isSourceLoaded('states')
        )
      );
    };
    const onSourceData = () => {
      setSourceLoadedForMap();
    };
    map?.on('sourcedata', onSourceData);
    return () => {
      map?.off('sourcedata', onSourceData);
    };
  }, [map]);

  useEffect(() => {
    // This effect colors the zones based on the co2 intensity
    if (!map || isLoading || isError) {
      return;
    }
    map?.touchZoomRotate.disableRotation();
    map?.touchPitch.disable();

    map.loadImage('/images/solar_asset.png', (error, image) => {
      if (error) {
        throw error;
      }
      if (image && !map.getImage('solar-asset-icon')) {
        map.addImage('solar-asset-icon', image);
      }
    });

    if (!isSourceLoaded || isLoadingMap) {
      return;
    }
    for (const feature of worldGeometries.features) {
      const { zoneId } = feature.properties;
      const zone = data?.datetimes[selectedDatetimeString]?.z[zoneId];
      const co2intensity = zone ? getCarbonIntensity(zone, isConsumption) : undefined;
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
    map,
    data,
    getCo2colorScale,
    isLoadingMap,
    isSourceLoaded,
    spatialAggregate,
    isSuccess,
    isLoading,
    isError,
    worldGeometries.features,
    theme.clickableFill,
    selectedDatetimeString,
    isConsumption,
  ]);

  useEffect(() => {
    // Run on first load to center the map on the user's location
    if (!map || isError || !isFirstLoad || !isSourceLoaded || !userLocation) {
      return;
    }
    if (!selectedZoneId) {
      map.flyTo({ center: [userLocation[0], userLocation[1]] });

      const handleIdle = () => {
        if (map.isSourceLoaded(ZONE_SOURCE) && map.areTilesLoaded()) {
          const source = map.getSource(ZONE_SOURCE);
          const layer = map.getLayer('zones-clickable-layer');
          if (!source) {
            console.error(`Source "${ZONE_SOURCE}" not found`);
            return;
          }
          if (!layer) {
            console.error('Layer "zones-clickable-layer" not found or not rendered');
            return;
          }
          const zoneFeature = getZoneIdFromLocation(map, userLocation, ZONE_SOURCE);
          if (zoneFeature) {
            const zoneId = zoneFeature.properties.zoneId;
            setUserLocation(zoneId);
          }
          map.off('idle', handleIdle);
        }
      };
      setIsFirstLoad(false);
      map.on('idle', handleIdle);
    }
  }, [
    map,
    isSuccess,
    isError,
    isFirstLoad,
    userLocation,
    selectedZoneId,
    isSourceLoaded,
    setUserLocation,
  ]);

  useEffect(() => {
    // Run when the selected zone changes
    // deselect and dehover zone when navigating to /map (e.g. using back button on mobile panel)
    if (map && location.pathname.startsWith('/map') && selectedZoneId) {
      map.setFeatureState(
        { source: ZONE_SOURCE, id: selectedZoneId },
        { selected: false, hover: false }
      );
      setHoveredZone(null);
    }
    // Center the map on the selected zone

    setSelectedZoneId(pathZoneId);
    if (map && !isLoadingMap && pathZoneId) {
      const feature = worldGeometries.features.find(
        (feature) => feature?.properties?.zoneId === pathZoneId
      );
      // if no feature matches, it means that the selected zone is not in current spatial resolution.
      // We cannot include geometries in dependencies, as we don't want to flyTo when user switches
      // between spatial resolutions. Therefore we find an approximate feature based on the zoneId.
      if (feature) {
        const center = feature.properties.center;
        map.setFeatureState({ source: ZONE_SOURCE, id: pathZoneId }, { selected: true });
        setLeftPanelOpen(true);
        const centerMinusLeftPanelWidth = [center[0] - 10, center[1]] as [number, number];
        map.flyTo({ center: isMobile ? center : centerMinusLeftPanelWidth, zoom: 3.5 });
      }
    }
  }, [
    map,
    location.pathname,
    isLoadingMap,
    selectedZoneId,
    setHoveredZone,
    worldGeometries.features,
    setLeftPanelOpen,
    pathZoneId,
  ]);

  const onClick = useCallback(
    ({ features }: maplibregl.MapLayerMouseEvent) => {
      if (!map || !features) {
        return;
      }
      const feature = features[0];

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
      if (feature?.properties) {
        const zoneId = feature.properties.zoneId;
        // Do not keep hash on navigate so that users are not scrolled to id element in new view
        navigate({ to: '/zone', zoneId, keepHashParameters: false });
      } else {
        navigate({ to: '/map', keepHashParameters: false });
      }
    },
    [map, selectedZoneId, hoveredZone, setHoveredZone, navigate]
  );

  // TODO: Consider if we need to ignore zone hovering if the map is dragging
  const onMouseMove = useCallback(
    ({ features, point }: maplibregl.MapLayerMouseEvent) => {
      if (!map || !features) {
        return;
      }
      const feature = features[0];
      const isHoveringAZone = feature?.id !== undefined;
      const isHoveringANewZone =
        isHoveringAZone && hoveredZone?.featureId !== feature?.id;

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
        x: point.x,
        y: point.y,
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
    },
    [map, hoveredZone, setHoveredZone, setMousePosition]
  );

  const onMouseOut = useCallback(() => {
    if (!map) {
      return;
    }

    // Reset hovered state when mouse leaves map (e.g., cursor moving into panel)
    if (hoveredZone?.featureId !== undefined) {
      map.setFeatureState(
        { source: ZONE_SOURCE, id: hoveredZone?.featureId },
        { hover: false }
      );
      setHoveredZone(null);
    }
  }, [map, hoveredZone, setHoveredZone]);

  const onError = useCallback(
    ({ error }: ErrorEvent) => {
      console.error(error);
      setIsLoadingMap(false);
      // TODO: Show error message to user
      // TODO: Send to Sentry
      // TODO: Handle the "no webgl" error gracefully
    },
    [setIsLoadingMap]
  );

  const onLoad = useCallback(() => {
    setIsLoadingMap(false);
    if (onMapLoad && mapReference) {
      onMapLoad(mapReference.getMap());
    }
  }, [setIsLoadingMap, onMapLoad, mapReference]);

  const onMoveStart = useCallback(() => {
    setIsMoving(true);
  }, [setIsMoving]);

  const onMoveEnd = useCallback(() => {
    setIsMoving(false);
  }, [setIsMoving]);

  return (
    <Map
      RTLTextPlugin={false}
      ref={onMapReferenceChange}
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
      onMoveStart={onMoveStart}
      onMoveEnd={onMoveEnd}
      dragPan={{ maxSpeed: 0 }} // Disables easing effect to improve performance on exchange layer
      dragRotate={false}
      minZoom={0.7}
      maxBounds={[
        [Number.NEGATIVE_INFINITY, SOUTHERN_LATITUDE_BOUND],
        [Number.POSITIVE_INFINITY, NORTHERN_LATITUDE_BOUND],
      ]}
      style={{
        minWidth: `calc(100vw - ${SIDEBAR_WIDTH})`,
        height: '100vh',
        position: 'absolute',
      }}
      mapStyle={MAP_STYLE as StyleSpecification}
    >
      <BackgroundLayer />
      <ZonesLayer />
      <StatesLayer />
      <SolarAssetsLayer />
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
