import React, {
  useState,
  useMemo,
  useRef,
  useEffect,
} from 'react';
import { Portal } from 'react-portal';
import ReactMapGL, { NavigationControl, Source, Layer } from 'react-map-gl';
import {
  isEmpty,
  map,
  noop,
  size,
} from 'lodash';

const interactiveLayerIds = ['zones-clickable'];
const mapStyle = { version: 8, sources: {}, layers: [] };

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
  theme = {},
  transitionDuration = 0,
  viewport = {
    latitude: 0,
    longitude: 0,
    zoom: 2,
  },
  zones = {},
}) => {
  const ref = useRef(null);
  const [hoveredZoneId, setHoveredZoneId] = useState(null);

  // Generate two sources (clickable and non-clickable zones), based on the zones data.
  const sources = useMemo(
    () => {
      const features = map(zones, (zone, zoneId) => ({
        type: 'Feature',
        geometry: {
          ...zone.geometry,
          coordinates: zone.geometry.coordinates.filter(size), // Remove empty geometries
        },
        properties: {
          color: zone.color,
          isClickable: zone.isClickable,
          zoneData: zone,
          zoneId,
        },
      }));

      return {
        zonesClickable: {
          type: 'FeatureCollection',
          features: features.filter(f => f.properties.isClickable),
        },
        zonesNonClickable: {
          type: 'FeatureCollection',
          features: features.filter(f => !f.properties.isClickable),
        },
      };
    },
    [zones],
  );

  // Every time the hovered zone changes, update the hover map layer accordingly.
  const hoverFilter = useMemo(() => (['==', 'zoneId', hoveredZoneId || '']), [hoveredZoneId]);

  // Calculate layer styles only when the theme changes
  // to keep the stable and prevent excessive rerendering.
  const styles = useMemo(
    () => ({
      hover: { 'fill-color': 'white', 'fill-opacity': 0.3 },
      ocean: { 'background-color': theme.oceanColor },
      zonesBorder: { 'line-color': theme.strokeColor, 'line-width': theme.strokeWidth },
      zonesClickable: { 'fill-color': ['case', ['has', 'color'], ['get', 'color'], theme.clickableFill] },
      zonesNonClickable: { 'fill-color': theme.nonClickableFill },
    }),
    [theme],
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
        maxZoom={10}
        onLoad={onMapLoaded}
        onClick={handleClick}
        onMouseMove={handleMouseMove}
        onMouseOut={handleMouseOut}
        onBlur={handleMouseOut}
        transitionDuration={transitionDuration}
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
        {/* Layers */}
        <Layer id="ocean" type="background" paint={styles.ocean} />
        <Source type="geojson" data={sources.zonesNonClickable}>
          <Layer id="zones-static" type="fill" paint={styles.zonesNonClickable} />
        </Source>
        <Source type="geojson" data={sources.zonesClickable}>
          <Layer id="zones-clickable" type="fill" paint={styles.zonesClickable} />
          <Layer id="zones-border" type="line" paint={styles.zonesBorder} />
          {/* Note: if stroke width is 1px, then it is faster to use fill-outline in fill layer */}
        </Source>
        <Source type="geojson" data={sources.zonesClickable}>
          <Layer id="hover" type="fill" paint={styles.hover} filter={hoverFilter} />
        </Source>
        {/* Extra layers provided by user */}
        {children}
      </ReactMapGL>
    </div>
  );
};

export default ZoneMap;
