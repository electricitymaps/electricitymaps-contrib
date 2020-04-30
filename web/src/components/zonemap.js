import React, {
  useState,
  useMemo,
  useRef,
  useEffect,
} from 'react';
import { useSelector } from 'react-redux';
import ReactMapGL, { NavigationControl } from 'react-map-gl';
import { isEmpty, noop } from 'lodash';

import { useCo2ColorScale, useTheme } from '../hooks/theme';
import { useZoneGeometries } from '../hooks/map';

const interactiveLayerIds = ['clickable-zones-fill'];

const ZoneMap = ({
  children = null,
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
  viewport = {
    latitude: 0,
    longitude: 0,
    zoom: 1.5,
  },
}) => {
  const ref = useRef();
  const isMobile = useSelector(state => state.application.isMobile);
  const zones = useSelector(state => state.data.grid.zones);
  const zoneGeometries = useZoneGeometries();
  const co2Scale = useCo2ColorScale();
  const theme = useTheme();

  const [hoveredZoneId, setHoveredZoneId] = useState(null);

  const staticMapStyle = useMemo(
    () => ({
      version: 8,
      sources: {
        'clickable-world': {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: zoneGeometries.clickable,
          },
        },
        'non-clickable-world': {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: zoneGeometries.nonClickable,
          },
        },
        // Duplicating source makes filter operations faster https://github.com/mapbox/mapbox-gl-js/issues/5040#issuecomment-321688603
        'hover': {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: zoneGeometries.clickable,
          },
        },
      },
      layers: [
        {
          id: 'background',
          type: 'background',
          paint: { 'background-color': theme.oceanColor },
        },
        {
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
        },
        {
          id: 'non-clickable-zones-fill',
          type: 'fill',
          source: 'non-clickable-world',
          layout: {},
          paint: { 'fill-color': theme.nonClickableFill },
        },
        {
          id: 'zones-hover',
          type: 'fill',
          source: 'hover',
          layout: {},
          paint: {
            'fill-color': 'white',
            'fill-opacity': 0.3,
          },
          filter: ['==', 'zoneId', ''],
        },
        // Note: if stroke width is 1px, then it is faster to use fill-outline in fill layer
        {
          id: 'zones-line',
          type: 'line',
          source: 'clickable-world',
          layout: {},
          paint: {
            'line-color': theme.strokeColor,
            'line-width': theme.strokeWidth,
          },
        },
      ],
    }),
    [zoneGeometries, theme, co2Scale],
  );

  // Update only the hovered zone in the zones-hover layer, keeping
  // the rest of the layers unchanged for more optimized layers diff
  // resolution in the ReactMapGL component.
  // TODO: Write this in a nicer way.
  const mapStyle = useMemo(
    () => ({
      ...staticMapStyle,
      layers: [
        staticMapStyle.layers[0],
        staticMapStyle.layers[1],
        staticMapStyle.layers[2],
        {
          ...staticMapStyle.layers[3],
          filter: ['==', 'zoneId', hoveredZoneId || ''],
        },
        staticMapStyle.layers[4],
      ],
    }),
    [staticMapStyle, hoveredZoneId],
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
      // Disable when dragging
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
      // Disable for touch devices
      if (ref.current && !isMobile) {
        onMouseMove({
          x: e.point[0],
          y: e.point[1],
          longitude: e.lngLat[0],
          latitude: e.lngLat[1],
        });
        // Trigger onZoneMouseEnter is mouse enters a different
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
    [ref.current, isMobile, hoveringEnabled, zones, hoveredZoneId, onMouseMove, onZoneMouseEnter, onZoneMouseLeave],
  );

  // TODO: Don't propagate navigation buttons mouse interaction events to the map.
  // TODO: Consider passing zoneGeometries as a prop.
  // TODO: Re-enable smooth animations.

  return (
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
      onViewportChange={onViewportChange}
    >
      <div className="mapboxgl-zoom-controls">
        <NavigationControl showCompass={false} />
      </div>
      {children}
    </ReactMapGL>
  );
};

export default ZoneMap;
