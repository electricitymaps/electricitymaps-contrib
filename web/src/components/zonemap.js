import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Portal } from 'react-portal';
import ReactMapGL, { NavigationControl, Source, Layer } from 'react-map-gl';
import { debounce, isEmpty, map, noop, size } from 'lodash';
import { __ } from '../helpers/translation';

const interactiveLayerIds = ['zones-clickable'];
const mapStyle = { version: 8, sources: {}, layers: [] };

const ZoneMap = ({
  children = null,
  hoveringEnabled = true,
  onMapLoaded = noop,
  onMapError = noop,
  onMouseMove = noop,
  onResize = noop,
  onSeaClick = noop,
  onViewportChange = noop,
  onZoneClick = noop,
  onZoneMouseEnter = noop,
  onZoneMouseLeave = noop,
  scrollZoom = true,
  style = {},
  theme = {},
  transitionDuration = 300,
  viewport = {
    latitude: 0,
    longitude: 0,
    zoom: 2,
  },
  zones = {},
}) => {
  const ref = useRef(null);
  const wrapperRef = useRef(null);
  const [hoveredZoneId, setHoveredZoneId] = useState(null);
  const [isSupported, setIsSupported] = useState(true);
  const [colorId, setColorId] = useState('color');
  const [remove, setRemove] = useState(false);

  const initialClickableStyle = () => ({
    // 'fill-color': ['case', ['has', 'color'], ['get', colorId], theme.clickableFill],
    'fill-color': [
      'case',
      ['boolean', ['feature-state', 'color'], false],
      [
        'interpolate',
        ['linear'],
        ['get', 'mag'],
        1,
        '#CE9443',
        1.5,
        '#D4661D',
        2,
        '#930000',
        2.5,
        '#FF7300',
        3,
        '#fc8d59',
        3.5,
        '#ef6548',
        4.5,
        '#d7301f',
        6.5,
        '#b30000',
        8.5,
        '#7f0000',
      ],
      'black',
    ],
  });
  // const initialClickableStyle = () => ({
  //   'fill-color':
  //   ['case', ['has', 'color'], `#${Math.floor(Math.random() * 16777215).toString(16)}`, theme.clickableFill]
  // })
  const [clickableStyle, setClickableStyle] = useState(initialClickableStyle());

  const [isDragging, setIsDragging] = useState(false);
  const debouncedSetIsDragging = useMemo(
    () =>
      debounce((value) => {
        setIsDragging(value);
      }, 200),
    []
  );

  // TODO: Try tying this to internal map state somehow to remove the need for these handlers.
  const handleDragStart = useMemo(() => () => setIsDragging(true), []);
  const handleDragEnd = useMemo(() => () => setIsDragging(false), []);
  const handleWheel = useMemo(
    () => () => {
      setIsDragging(true);
      debouncedSetIsDragging(false);
    },
    []
  );

  function randomRGB() {
    var o = Math.round,
      r = Math.random,
      s = 255;
    return `rgb(${o(r() * s)},${o(r() * s)},${o(r() * s)})`;
  }

  // Generate two sources (clickable and non-clickable zones), based on the zones data.
  const sources = useMemo(() => {
    console.log('Generate features');
    const features = map(zones, (zone, zoneId) => ({
      type: 'Feature',
      id: zoneId,
      geometry: {
        ...zone.geometry,
        coordinates: zone.geometry.coordinates.filter(size), // Remove empty geometries
      },
      properties: {
        color: randomRGB(),
        color2: randomRGB(),
        mag: Math.floor(Math.random() * 8),
        isClickable: zone.isClickable,
        zoneData: zone,
        zoneId,
      },
    }));

    return {
      zonesClickable: {
        type: 'FeatureCollection',
        features: features.filter((f) => f.properties.isClickable),
      },
      zonesNonClickable: {
        type: 'FeatureCollection',
        features: features.filter((f) => !f.properties.isClickable),
      },
    };
  }, [zones]);

  // Every time the hovered zone changes, update the hover map layer accordingly.
  const hoverFilter = useMemo(() => ['==', 'zoneId', hoveredZoneId || ''], [hoveredZoneId]);

  // Calculate layer styles only when the theme changes
  // to keep the stable and prevent excessive rerendering.
  const styles = useMemo(
    () => ({
      hover: { 'fill-color': 'white', 'fill-opacity': 0.3 },
      ocean: { 'background-color': theme.oceanColor },
      zonesBorder: { 'line-color': theme.strokeColor, 'line-width': theme.strokeWidth },
      zonesNonClickable: { 'fill-color': theme.nonClickableFill },
    }),
    [theme]
  );

  // If WebGL is not supported trigger an error callback.
  useEffect(() => {
    if (!ReactMapGL.supported()) {
      setIsSupported(false);
      onMapError('WebGL not supported');
    }
  }, []);

  
  const coloring = (e) => {
    setRemove(!remove);
    const features = ref.current.queryRenderedFeatures();
    const map = ref.current.getMap();
    console.log(remove);
    features.forEach((ft) => {
      const ftId = ft.id;
      if (remove) {
        map.removeFeatureState({
          source: 'zones-clickable',
          id: ftId,
        });
      } else {
        map.setFeatureState(
          {
            source: 'zones-clickable',
            id: ftId,
          },
          {
            color: true,
          }
        );
      }
    });
  };

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
    [ref.current, onSeaClick, onZoneClick]
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
        // Ignore zone hovering when dragging (performance optimization).
        if (!isDragging) {
          const features = ref.current.queryRenderedFeatures(e.point);
          // Trigger onZoneMouseEnter if mouse enters a different
          // zone and onZoneMouseLeave when it leaves all zones.
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
      }
    },
    [
      ref.current,
      hoveringEnabled,
      isDragging,
      zones,
      hoveredZoneId,
      onMouseMove,
      onZoneMouseEnter,
      onZoneMouseLeave,
    ]
  );

  const handleMouseOut = useMemo(
    () => () => {
      if (hoveredZoneId !== null) {
        onZoneMouseLeave();
        setHoveredZoneId(null);
      }
    },
    [hoveredZoneId]
  );

  // Don't render map nor any of the layers if WebGL is not supported.
  if (!isSupported) {
    return null;
  }

  return (
    <div className="zone-map" style={style} ref={wrapperRef}>
      <ReactMapGL
        ref={ref}
        width="100%"
        height="100%"
        latitude={viewport.latitude}
        longitude={viewport.longitude}
        zoom={viewport.zoom}
        interactiveLayerIds={interactiveLayerIds}
        dragRotate={false}
        touchRotate={false}
        scrollZoom={scrollZoom}
        mapStyle={mapStyle}
        maxZoom={10}
        onBlur={handleMouseOut}
        onClick={handleClick}
        onError={onMapError}
        onLoad={onMapLoaded}
        onMouseMove={handleMouseMove}
        onMouseOut={handleMouseOut}
        onMouseDown={handleDragStart}
        onMouseUp={handleDragEnd}
        onResize={onResize}
        onTouchStart={handleDragStart}
        onTouchEnd={handleDragEnd}
        onWheel={handleWheel}
        onViewportChange={onViewportChange}
        transitionDuration={isDragging ? 0 : transitionDuration}
      >
        {/*
          Render the navigation controls next to ReactMapGL in the DOM so that
          hovering over zoom buttons doesn't fire hover events on the map.
        */}
        <Portal node={wrapperRef.current}>
          <input
            type="range"
            min={0}
            max={24}
            className="color-button"
            style={{
              position: 'absolute',
              top: '20px',
              left: '500px',
              zIndex: '100',
              width: 300,
            }}
            onChange={() => {
              coloring();
            }}
          />
          <div
            className="mapboxgl-zoom-controls"
            style={{
              boxShadow: '0px 0px 10px 0px rgba(0,0,0,0.15)',
              position: 'absolute',
              right: '24px',
              top: '24px',
            }}
          >
            <NavigationControl
              showCompass={false}
              zoomInLabel={__('tooltips.zoomIn')}
              zoomOutLabel={__('tooltips.zoomOut')}
            />
          </div>
        </Portal>
        {/* Layers */}
        <Layer id="ocean" type="background" paint={styles.ocean} />
        <Source type="geojson" data={sources.zonesNonClickable}>
          <Layer id="zones-static" type="fill" paint={styles.zonesNonClickable} />
        </Source>
        <Source id="zones-clickable" generateId type="geojson" data={sources.zonesClickable}>
          <Layer id="zones-clickable" type="fill" paint={clickableStyle} />
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
