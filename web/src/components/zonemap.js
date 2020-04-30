import React, {
  useState,
  useMemo,
  useRef,
  useEffect,
} from 'react';
import { Portal } from 'react-portal';
import ReactMapGL, { NavigationControl } from 'react-map-gl';
import { isEmpty, filter, noop } from 'lodash';

const interactiveLayerIds = ['clickable-zones-fill'];

const ZoneMap = ({
  children = null,
  // TODO: Generalize this to a custom color function
  co2Scale = noop,
  hoveringEnabled = true,
  onMapLoaded = noop,
  onMapInitFailed = noop,
  onMouseMove = noop,
  onSeaClick = noop,
  onViewportChange = noop,
  onZoneClick = noop,
  onZoneMouseEnter = noop,
  onZoneMouseLeave = noop,
  scrollZoom = true,
  theme = {},
  viewport = {
    latitude: 0,
    longitude: 0,
    zoom: 1.5,
  },
  // TODO: Calculate this from zones
  zoneGeometries = { clickable: [], nonClickable: [] },
  zones = {},
}) => {
  const ref = useRef(null);
  const [hoveredZoneId, setHoveredZoneId] = useState(null);

  const clickableWorldSource = useMemo(
    () => ({
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: zoneGeometries.clickable,
      },
    }),
    [zoneGeometries.clickable],
  );

  const nonClickableWorldSource = useMemo(
    () => ({
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: zoneGeometries.nonClickable,
      },
    }),
    [zoneGeometries.nonClickable],
  );

  const hoveredZoneSource = useMemo(
    () => ({
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: filter(zoneGeometries.clickable, f => f.properties.zoneId === hoveredZoneId),
      },
    }),
    [hoveredZoneId, zoneGeometries.clickable],
  );

  const backgroundLayer = useMemo(
    () => ({
      id: 'background',
      type: 'background',
      paint: { 'background-color': theme.oceanColor },
    }),
    [theme.oceanColor],
  );

  const clickableZonesLayer = useMemo(
    () => ({
      id: 'clickable-zones-fill',
      type: 'fill',
      source: 'clickable-world',
      layout: {},
      paint: {
        'fill-color': {
          property: 'co2intensity',
          stops: [0, 200, 400, 600, 800, 1000].map(d => [d, co2Scale(d)]),
          default: theme.clickableFill,
        },
      },
    }),
    [co2Scale, theme.clickableFill],
  );

  const nonClickableZonesLayer = useMemo(
    () => ({
      id: 'non-clickable-zones-fill',
      type: 'fill',
      source: 'non-clickable-world',
      layout: {},
      paint: { 'fill-color': theme.nonClickableFill },
    }),
    [theme.nonClickableFill],
  );

  const zonesHoverLayer = useMemo(
    () => ({
      id: 'zones-hover',
      type: 'fill',
      source: 'hover',
      layout: {},
      paint: {
        'fill-color': 'white',
        'fill-opacity': 0.3,
      },
    }),
    [],
  );

  // Note: if stroke width is 1px, then it is faster to use fill-outline in fill layer
  const zonesLinesLayer = useMemo(
    () => ({
      id: 'zones-line',
      type: 'line',
      source: 'clickable-world',
      layout: {},
      paint: {
        'line-color': theme.strokeColor,
        'line-width': theme.strokeWidth,
      },
    }),
    [theme.strokeColor, theme.strokeWidth],
  );

  const mapStyle = useMemo(
    () => ({
      version: 8,
      sources: {
        'clickable-world': clickableWorldSource,
        'non-clickable-world': nonClickableWorldSource,
        'hover': hoveredZoneSource,
      },
      layers: [
        backgroundLayer,
        clickableZonesLayer,
        nonClickableZonesLayer,
        zonesHoverLayer,
        zonesLinesLayer,
      ],
    }),
    [
      clickableWorldSource,
      nonClickableWorldSource,
      hoveredZoneSource,
      backgroundLayer,
      clickableZonesLayer,
      nonClickableZonesLayer,
      zonesHoverLayer,
      zonesLinesLayer,
    ],
  );

  // If WebGL is not supported trigger a callback.
  useEffect(
    () => {
      if (!ReactMapGL.supported()) {
        onMapInitFailed();
      }
    },
    [],
  );

  const handleClick = useMemo(
    () => (e) => {
      if (ref.current && !ref.current.state.isDragging) {
        const features = ref.current.queryRenderedFeatures(e.point);
        if (isEmpty(features)) {
          onSeaClick();
        } else {
          onZoneClick(features[0].properties.zoneId);
        }
      }
    },
    [ref.current, onSeaClick, onZoneClick],
  );

  const handleMouseMove = useMemo(
    () => (e) => {
      if (ref.current) {
        if (hoveringEnabled) {
          onMouseMove({
            x: e.point[0],
            y: e.point[1],
            longitude: e.lngLat[0],
            latitude: e.lngLat[1],
          });
        }
        // Trigger onZoneMouseEnter if mouse enters a different
        // zone and onZoneMouseLeave when it leaves all zones.
        const features = ref.current.queryRenderedFeatures(e.point);
        if (!isEmpty(features) && hoveringEnabled) {
          const { zoneId } = features[0].properties;
          if (hoveredZoneId !== zoneId) {
            onZoneMouseEnter(zones[zoneId], zoneId);
            setHoveredZoneId(zoneId);
          }
        } else if (hoveredZoneId !== null) {
          onZoneMouseLeave();
          setHoveredZoneId(null);
        }
      }
    },
    [ref.current, hoveringEnabled, zones, hoveredZoneId, onMouseMove, onZoneMouseEnter, onZoneMouseLeave],
  );

  const handleMouseOut = useMemo(
    () => () => {
      if (hoveredZoneId !== null) {
        onZoneMouseLeave();
        setHoveredZoneId(null);
      }
    },
    [hoveredZoneId],
  );

  // TODO: Re-enable smooth animations.

  return (
    <div id="zone-map">
      <ReactMapGL
        ref={ref}
        width="100vw"
        height="100vh"
        latitude={viewport.latitude}
        longitude={viewport.longitude}
        zoom={viewport.zoom}
        interactiveLayerIds={interactiveLayerIds}
        dragRotate={false}
        touchRotate={false}
        scrollZoom={scrollZoom}
        mapStyle={mapStyle}
        onLoad={onMapLoaded}
        onClick={handleClick}
        onMouseMove={handleMouseMove}
        onMouseOut={handleMouseOut}
        onBlur={handleMouseOut}
        onViewportChange={onViewportChange}
      >
        {/*
          Render the navigation controls next to ReactMapGL in the DOM so that
          hovering over zoom buttons doesn't fire hover events on the map.
        */}
        <Portal node={document.getElementById('zone-map')}>
          <div className="mapboxgl-zoom-controls">
            <NavigationControl
              showCompass={false}
              zoomInLabel=""
              zoomOutLabel=""
            />
          </div>
        </Portal>
        {children}
      </ReactMapGL>
    </div>
  );
};

export default ZoneMap;
