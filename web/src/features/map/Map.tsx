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
import { ReactElement, useCallback, useEffect, useRef, useState } from 'react';
import { ErrorEvent, Map, MapRef } from 'react-map-gl/maplibre';
import { useLocation, useParams, useSearchParams } from 'react-router-dom';
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
  hoveredSolarAssetInfoAtom,
  hoveredZoneAtom,
  loadingMapAtom,
  mapMovingAtom,
  mousePositionAtom,
  selectedSolarAssetAtom,
} from './mapAtoms';
import { FeatureId } from './mapTypes';
import SolarAssetNameTooltip from './SolarAssetNameTooltip';

export const ZONE_SOURCE = 'zones-clickable';
export const SOLAR_ASSETS_SOURCE = 'solar-assets';
export const SOLAR_ASSETS_LAYER_ID = 'solar-assets-points';
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
  const [selectedSolarAsset, setSelectedSolarAsset] = useAtom(selectedSolarAssetAtom);
  const [hoveredSolarAssetInfoValue, setHoveredSolarAssetInfo] = useAtom(
    hoveredSolarAssetInfoAtom
  );
  const hoveredSolarAssetInfoValue = useAtomValue(hoveredSolarAssetInfoAtom);
  const setHoveredSolarAssetInfo = useSetAtom(hoveredSolarAssetInfoAtom);
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
  const [searchParameters] = useSearchParams();
  const solarAssetId = searchParameters.get('solarAssetId');
  const [wasInBackground, setWasInBackground] = useState(false);
  const previouslyHoveredAssetId = useRef<FeatureId | null>(null);

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

  // Center on solar asset from URL parameter OR from zoneId path parameter
  useEffect(() => {
    if (!map || isError || !isSourceLoaded) {
      return;
    }

    let assetIdFromPath = null;
    if (pathZoneId && pathZoneId.startsWith('solar-asset-')) {
      assetIdFromPath = decodeURIComponent(pathZoneId.replace('solar-asset-', ''));
    }

    const effectiveAssetId = assetIdFromPath || solarAssetId;

    if (effectiveAssetId && !selectedSolarAsset) {
      // If we are about to load a solar asset from the URL,
      // consider this the primary action for the first load.
      if (isFirstLoad) {
        setIsFirstLoad(false);
      }

      const waitForSourceData = () => {
        if (map.isSourceLoaded(SOLAR_ASSETS_SOURCE)) {
          try {
            // Get all features from the source
            const features = map.querySourceFeatures(SOLAR_ASSETS_SOURCE);

            // Find the feature with matching ID
            const feature = features.find(
              (f) =>
                String(f.id) === effectiveAssetId ||
                String(f.properties?.name) === effectiveAssetId
            );

            if (feature) {
              // Set the feature state to selected
              map.setFeatureState(
                {
                  source: SOLAR_ASSETS_SOURCE,
                  id: feature.id || feature.properties.name,
                },
                { selected: true }
              );

              // Get coordinates from the feature's geometry
              const coordinates =
                feature.geometry.type === 'Point'
                  ? ([...feature.geometry.coordinates] as [number, number])
                  : undefined;

              if (coordinates) {
                // Center the map on the solar asset with a higher zoom level
                map.flyTo({
                  center: coordinates,
                  zoom: 7, // Consistent zoom level with onClick
                  duration: 1000,
                });

                // Set the selected solar asset in state
                setSelectedSolarAsset({
                  id: String(feature.id || feature.properties.name),
                  properties: feature.properties as Record<string, any>,
                });

                map.setFeatureState(
                  {
                    source: SOLAR_ASSETS_SOURCE,
                    id: feature.id || feature.properties.name,
                  },
                  { selected: true }
                );
              } else {
                console.error(
                  `[Map.tsx] No valid coordinates found for feature with ID ${effectiveAssetId}`
                );
              }
            } else {
              // If we can't find the feature in the current viewport,
              // we need to try a different approach

              // Check if we've already tried multiple times
              const attempts = Number.parseInt(
                map.getCanvas().dataset.searchAttempts || '0',
                10
              );

              if (attempts < 10) {
                // Increment the attempt counter
                map.getCanvas().dataset.searchAttempts = String(attempts + 1);

                // Wait a bit longer for more data to load

                // Keep listening for source data events
                return;
              } else {
                console.error(
                  `[Map.tsx] Could not find asset with ID ${effectiveAssetId} after multiple attempts`
                );
                map.off('sourcedata', waitForSourceData);
              }
            }
          } catch (error) {
            console.error(`[Map.tsx] Error centering on solar asset:`, error);
            map.off('sourcedata', waitForSourceData);
          }
        }
      };

      // Reset the attempt counter
      map.getCanvas().dataset.searchAttempts = '0';

      // Try immediately and also listen for sourcedata events
      waitForSourceData();
      map.on('sourcedata', waitForSourceData);

      return () => {
        map.off('sourcedata', waitForSourceData);
      };
    }
  }, [
    map,
    solarAssetId,
    pathZoneId,
    isSourceLoaded,
    isError,
    selectedSolarAsset,
    setSelectedSolarAsset,
    isFirstLoad,
    setIsFirstLoad,
  ]);

  const onClick = useCallback(
    ({ features }: maplibregl.MapLayerMouseEvent) => {
      const map = mapReference?.getMap();
      if (!map) {
        return;
      }
      // Clear previously hovered asset on any click
      if (previouslyHoveredAssetId.current) {
        map.setFeatureState(
          { source: SOLAR_ASSETS_SOURCE, id: previouslyHoveredAssetId.current },
          { hover: false }
        );
        previouslyHoveredAssetId.current = null;
        setHoveredSolarAssetInfo(null);
      }

      // If clicking on empty space (no features)
      if (!features || features.length === 0) {
        // Clear zone selection if there was one
        if (selectedZoneId) {
          map.setFeatureState(
            { source: ZONE_SOURCE, id: selectedZoneId },
            { selected: false }
          );
        }
        // Clear solar asset selection if there was one
        if (selectedSolarAsset) {
          map.setFeatureState(
            { source: SOLAR_ASSETS_SOURCE, id: selectedSolarAsset.id },
            { selected: false }
          );
          setSelectedSolarAsset(null);
        }
        // Only clear URL parameters if we actually had a selection before
        if (pathZoneId || solarAssetId) {
          navigate({ to: '/map', keepHashParameters: false });
          // Clear the search parameter
          window.history.replaceState(null, '', window.location.pathname);
        }
        return;
      }

      const clickedZoneFeature = features.find((f) => f.source === ZONE_SOURCE);
      const clickedSolarAssetFeature = features.find(
        (f) => f.layer.id === SOLAR_ASSETS_LAYER_ID
      );

      // Prioritize solar asset click if available
      if (
        clickedSolarAssetFeature &&
        clickedSolarAssetFeature.id !== undefined &&
        clickedSolarAssetFeature.properties
      ) {
        const assetId = clickedSolarAssetFeature.id;
        const assetProperties = clickedSolarAssetFeature.properties;

        if (selectedZoneId) {
          map.setFeatureState(
            { source: ZONE_SOURCE, id: selectedZoneId },
            { selected: false, hover: false }
          );
          // If a zone was selected (e.g. panel open), and we click an asset,
          // navigate to base map to close zone panel implicitly.
          if (pathZoneId) {
            navigate({ to: '/map', keepHashParameters: false });
          }
        }

        if (selectedSolarAsset && selectedSolarAsset.id !== assetId) {
          map.setFeatureState(
            { source: SOLAR_ASSETS_SOURCE, id: selectedSolarAsset.id },
            { selected: false }
          );
        }

        map.setFeatureState(
          { source: SOLAR_ASSETS_SOURCE, id: assetId },
          { selected: true }
        );
        setSelectedSolarAsset({
          id: assetId,
          properties: assetProperties as Record<string, any>,
        });

        // Create a special identifier for the solar asset that can be parsed
        const solarAssetParameter = `solar-asset-${encodeURIComponent(String(assetId))}`;

        // Only update URL if we need to (prevents unnecessary navigation)
        if (pathZoneId !== solarAssetParameter) {
          // Navigate to the zone path with the solar asset ID as part of the path
          navigate({
            to: '/zone',
            zoneId: solarAssetParameter,
            keepHashParameters: false,
          });
        }

        // Center map on the solar asset if we have coordinates
        const coordinates =
          clickedSolarAssetFeature.geometry?.type === 'Point'
            ? ([...clickedSolarAssetFeature.geometry.coordinates] as [number, number])
            : undefined;

        if (coordinates) {
          map.flyTo({
            center: coordinates,
            zoom: 7, // Higher zoom level for solar assets
            duration: 1000,
          });
        }
      } else if (clickedZoneFeature) {
        // Only handle zone click if no solar asset was clicked
        const newZoneId = clickedZoneFeature.properties.zoneId;
        if (selectedSolarAsset) {
          map.setFeatureState(
            { source: SOLAR_ASSETS_SOURCE, id: selectedSolarAsset.id },
            { selected: false }
          );
          setSelectedSolarAsset(null); // Clear selected asset if now clicking a zone

          // Clear the solar asset search parameter when switching to a zone
          window.history.replaceState(null, '', window.location.pathname);
        }

        if (selectedZoneId && selectedZoneId !== newZoneId) {
          map.setFeatureState(
            { source: ZONE_SOURCE, id: selectedZoneId },
            { selected: false }
          );
        }

        navigate({ to: '/zone', zoneId: newZoneId, keepHashParameters: false });
      } else {
        // Clicked on map, but not on a zone or solar asset specifically
        if (selectedZoneId) {
          map.setFeatureState(
            { source: ZONE_SOURCE, id: selectedZoneId },
            { selected: false }
          );
        }
        if (selectedSolarAsset) {
          map.setFeatureState(
            { source: SOLAR_ASSETS_SOURCE, id: selectedSolarAsset.id },
            { selected: false }
          );
          setSelectedSolarAsset(null);
        }
        if (pathZoneId || solarAssetId) {
          navigate({ to: '/map', keepHashParameters: false });
          // Clear the search parameter
          window.history.replaceState(null, '', window.location.pathname);
        }
      }

      if (hoveredZone) {
        map.setFeatureState(
          { source: ZONE_SOURCE, id: hoveredZone.featureId },
          { hover: false }
        );
        setHoveredZone(null);
      }
    },
    [
      mapReference,
      selectedZoneId,
      hoveredZone,
      setHoveredZone,
      navigate,
      selectedSolarAsset,
      setSelectedSolarAsset,
      pathZoneId,
      setHoveredSolarAssetInfo,
      solarAssetId,
    ]
  );

  const onMouseMove = useCallback(
    ({ features, point }: maplibregl.MapLayerMouseEvent) => {
      const map = mapReference?.getMap();
      if (!map) {
        return;
      }

      const zoneFeature = features?.find((f) => f.source === ZONE_SOURCE);
      const solarAssetFeature = features?.find(
        (f) => f.layer.id === SOLAR_ASSETS_LAYER_ID
      );

      setMousePosition({ x: point.x, y: point.y });

      if (solarAssetFeature) {
        const properties = (solarAssetFeature.properties as Record<string, any>) || {};
        const assetInfo = {
          properties,
          x: point.x,
          y: point.y,
        };
        setHoveredSolarAssetInfo(assetInfo);

        if (hoveredZone) {
          map.setFeatureState(
            { source: ZONE_SOURCE, id: hoveredZone.featureId },
            { hover: false }
          );
          setHoveredZone(null);
        }

        if (solarAssetFeature.id === undefined) {
          if (previouslyHoveredAssetId.current) {
            map.setFeatureState(
              { source: SOLAR_ASSETS_SOURCE, id: previouslyHoveredAssetId.current },
              { hover: false }
            );
            previouslyHoveredAssetId.current = null;
          }
        } else {
          const currentAssetId = solarAssetFeature.id;
          if (previouslyHoveredAssetId.current !== currentAssetId) {
            if (previouslyHoveredAssetId.current) {
              map.setFeatureState(
                { source: SOLAR_ASSETS_SOURCE, id: previouslyHoveredAssetId.current },
                { hover: false }
              );
            }
            map.setFeatureState(
              { source: SOLAR_ASSETS_SOURCE, id: currentAssetId },
              { hover: true }
            );
            previouslyHoveredAssetId.current = currentAssetId;
          }
        }
      } else if (zoneFeature && zoneFeature.id !== undefined) {
        const newHoveredZoneId = zoneFeature.id;
        if (hoveredZone?.featureId !== newHoveredZoneId) {
          if (hoveredZone) {
            map.setFeatureState(
              { source: ZONE_SOURCE, id: hoveredZone.featureId },
              { hover: false }
            );
          }
          setHoveredZone({
            featureId: newHoveredZoneId,
            zoneId: zoneFeature.properties?.zoneId,
          });
          map.setFeatureState(
            { source: ZONE_SOURCE, id: newHoveredZoneId },
            { hover: true }
          );
        }
        if (previouslyHoveredAssetId.current) {
          map.setFeatureState(
            { source: SOLAR_ASSETS_SOURCE, id: previouslyHoveredAssetId.current },
            { hover: false }
          );
          previouslyHoveredAssetId.current = null;
        }
        setHoveredSolarAssetInfo(null);
      } else {
        if (hoveredZone) {
          map.setFeatureState(
            { source: ZONE_SOURCE, id: hoveredZone.featureId },
            { hover: false }
          );
          setHoveredZone(null);
        }
        if (previouslyHoveredAssetId.current) {
          map.setFeatureState(
            { source: SOLAR_ASSETS_SOURCE, id: previouslyHoveredAssetId.current },
            { hover: false }
          );
          previouslyHoveredAssetId.current = null;
        }
        setHoveredSolarAssetInfo(null);
      }
    },
    [
      mapReference,
      hoveredZone,
      setHoveredZone,
      setMousePosition,
      setHoveredSolarAssetInfo,
    ]
  );

  const onMouseOut = useCallback(() => {
    const map = mapReference?.getMap();
    if (!map) {
      return;
    }

    if (hoveredZone) {
      map.setFeatureState(
        { source: ZONE_SOURCE, id: hoveredZone.featureId },
        { hover: false }
      );
      setHoveredZone(null);
    }
    if (previouslyHoveredAssetId.current) {
      map.setFeatureState(
        { source: SOLAR_ASSETS_SOURCE, id: previouslyHoveredAssetId.current },
        { hover: false }
      );
      previouslyHoveredAssetId.current = null;
    }
    setHoveredSolarAssetInfo(null);
  }, [mapReference, hoveredZone, setHoveredZone, setHoveredSolarAssetInfo]);

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
      interactiveLayerIds={[
        'zones-clickable-layer',
        'zones-hoverable-layer',
        SOLAR_ASSETS_LAYER_ID,
      ]}
      cursor={hoveredZone || hoveredSolarAssetInfoValue ? 'pointer' : 'grab'}
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
        <SolarAssetsLayer />
      </CustomLayer>
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
      <SolarAssetNameTooltip />
    </Map>
  );
}
