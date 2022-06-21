import React, { useState, useMemo, useRef, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Portal } from 'react-portal';
import ReactMapGL, { Source, Layer } from 'react-map-gl';
import { noop } from '../helpers/noop';
import { isEmpty } from '../helpers/isEmpty';
import { debounce } from '../helpers/debounce';
import { ZoomControls } from './zoomcontrols';

const interactiveLayerIds = ['zones-clickable-layer'];
const mapStyle = { version: 8, sources: {}, layers: [] };

const ZoneMap = ({
  children = null,
  co2ColorScale = null,
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
  selectedZoneTimeIndex = null,
  style = {},
  theme = {},
  transitionDuration = 300,
  viewport = {
    latitude: 0,
    longitude: 0,
    zoom: 2,
  },
}) => {
  const ref = useRef(null);
  const wrapperRef = useRef(null);
  const [hoveredZoneId, setHoveredZoneId] = useState(null);
  const [isSupported, setIsSupported] = useState(true);
  const [isLoaded, setIsLoaded] = useState(false);
  const selectedTimeAggregate = useSelector((state) => state.application.selectedTimeAggregate);
  const zones = useSelector((state) => state.data.zones);

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
    [] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const handleLoad = () => {
    setIsLoaded(true);
    onMapLoaded();
  };

  // Generate two sources (clickable and non-clickable zones), based on the zones data.
  const sources = useMemo(() => {
    const features = Object.entries(zones).map(([zoneId, zone]) => {
      const length = (coordinate) => (coordinate ? coordinate.length : 0);
      return {
        type: 'Feature',
        geometry: {
          ...zone.geography.geometry,
          coordinates: zone.geography.geometry.coordinates.filter(length), // Remove empty geometries
        },
        properties: {
          color: undefined,
          zoneData: zone[selectedTimeAggregate].overviews,
          zoneId,
        },
      };
    });

    return {
      // TODO: Clean up further
      zonesClickable: {
        type: 'FeatureCollection',
        features,
      },
    };
  }, [zones, selectedTimeAggregate]);

  // Every time the hovered zone changes, update the hover map layer accordingly.
  const hoverFilter = useMemo(() => ['==', 'zoneId', hoveredZoneId || ''], [hoveredZoneId]);

  // Calculate layer styles only when the theme changes
  // to keep the stable and prevent excessive rerendering.
  const styles = useMemo(
    () => ({
      hover: { 'fill-color': 'white', 'fill-opacity': 0.3 },
      ocean: { 'background-color': theme.oceanColor },
      zonesBorder: { 'line-color': theme.strokeColor, 'line-width': theme.strokeWidth },
      zonesClickable: {
        'fill-color': [
          'coalesce', // // https://docs.mapbox.com/mapbox-gl-js/style-spec/expressions/#coalesce
          ['feature-state', 'color'],
          ['get', 'color'],
          theme.clickableFill,
        ],
      },
    }),
    [theme]
  );

  // If WebGL is not supported trigger an error callback.
  useEffect(() => {
    if (!ReactMapGL.supported()) {
      setIsSupported(false);
      onMapError('WebGL not supported');
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // TODO: Consider moving the calculation to a useMemo function
  // change color of zones if timeslider is changed
  useEffect(() => {
    if (isLoaded && co2ColorScale) {
      // TODO: This will only change RENDERED zones, so if you change the time in Europe and zoom out, go to US, it will not be updated!
      // TODO: Consider using isdragging or similar to update this when new zones are rendered
      const features = ref.current.queryRenderedFeatures();
      const map = ref.current.getMap();
      features.forEach((feature) => {
        const { color, zoneId } = feature.properties;
        let fillColor = color;
        const co2intensity = zones?.[zoneId]?.[selectedTimeAggregate]?.overviews[selectedZoneTimeIndex]?.co2intensity;
        // Calculate new color if zonetime is selected and we have a co2intensity
        if (selectedZoneTimeIndex !== null && co2intensity) {
          fillColor = co2ColorScale(co2intensity);
        }
        const existingColor = feature.id
          ? map.getFeatureState({ source: 'zones-clickable', id: feature.id }, 'color')?.color
          : color;

        if (feature.id && fillColor !== existingColor) {
          map.setFeatureState(
            {
              source: 'zones-clickable',
              id: feature.id,
            },
            {
              color: fillColor,
            }
          );
        }
      });
    }
  }, [isLoaded, isDragging, selectedTimeAggregate, co2ColorScale, zones, selectedZoneTimeIndex]);

  const handleClick = useMemo(
    () => (e) => {
      if (ref.current && ref.current.state && !ref.current.state.isDragging) {
        const features = ref.current.queryRenderedFeatures(e.point);
        if (isEmpty(features)) {
          onSeaClick();
        } else {
          onZoneClick(features[0].properties.zoneId);
        }
      }
    },
    [onSeaClick, onZoneClick]
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
              onZoneMouseEnter(zoneId);
              setHoveredZoneId(zoneId);
            }
          } else if (hoveredZoneId !== null) {
            onZoneMouseLeave();
            setHoveredZoneId(null);
          }
        }
      }
    },
    [hoveringEnabled, isDragging, hoveredZoneId, onMouseMove, onZoneMouseEnter, onZoneMouseLeave]
  );

  const handleMouseOut = useMemo(
    () => () => {
      if (hoveredZoneId !== null) {
        onZoneMouseLeave();
        setHoveredZoneId(null);
      }
    },
    [hoveredZoneId] // eslint-disable-line react-hooks/exhaustive-deps
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
        onLoad={handleLoad}
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
          <ZoomControls />
        </Portal>
        {/* Layers */}
        <Layer id="ocean" type="background" paint={styles.ocean} />
        <Source id="zones-clickable" generateId type="geojson" data={sources.zonesClickable}>
          <Layer id="zones-clickable-layer" type="fill" paint={styles.zonesClickable} />
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
