import React, { useState, useMemo, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import ReactMapGL from 'react-map-gl';
import { isEmpty, noop } from 'lodash';

import thirdPartyServices from '../services/thirdparty';
import { navigateTo } from '../helpers/router';
import { useCo2ColorScale, useTheme } from '../hooks/theme';
import { useZoneGeometries } from '../hooks/map';
import { dispatch, dispatchApplication } from '../store';

import { MAP_COUNTRY_TOOLTIP_KEY } from '../helpers/constants';

const interactiveLayerIds = ['clickable-zones-fill'];

const Map = ({
  scrollZoom = true,
  onMapLoaded = noop,
  onSeaClick = noop,
  onZoneClick = noop,
  onZoneMouseMove = noop,
  onZoneMouseOut = noop,
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
          filter: ['==', 'zoneId', 'DE'],
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

  const [viewport, setViewport] = useState({
    latitude: 50,
    longitude: 0,
    zoom: 1.5,
  });

  const handleClick = useMemo(
    () => ({ point }) => {
      // Disable when dragging
      if (ref.current && !ref.current.state.isDragging) {
        const features = ref.current.queryRenderedFeatures(point);
        if (isEmpty(features)) {
          onSeaClick();
        } else {
          onZoneClick(features[0].properties.zoneId);
        }
      }
    },
    [ref.current],
  );

  const handleMouseMove = useMemo(
    () => ({ point }) => {
      // Disable for touch devices
      if (ref.current && !isMobile) {
        const features = ref.current.queryRenderedFeatures(point);
        if (!isEmpty(features)) {
          const { zoneId } = features[0].properties;
          if (hoveredZoneId !== zoneId) {
            setHoveredZoneId(zoneId);
          }
          onZoneMouseMove(zones[zoneId], zoneId, point[0], point[1]);
        }
      }
    },
    [ref.current, isMobile, zones],
  );

  const handleMouseLeave = useMemo(
    () => () => {
      // Disable for touch devices
      if (!isMobile) {
        if (hoveredZoneId !== null) {
          setHoveredZoneId(null);
        }
        onZoneMouseOut();
      }
    },
    [isMobile],
  );

  // TODO: Detect WebGL support.
  // TODO: Add navigation control.
  // TODO: Put viewport state in Redux.
  // TODO: Add tooltip.
  // TODO: Add onMouseMove handler.
  // TODO: Consider passing zoneGeometries as a prop.
  // TODO: Re-enable layers.

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
      onMouseLeave={handleMouseLeave}
      onViewportChange={setViewport}
    />
  );
};

export default () => {
  const electricityMixMode = useSelector(state => state.application.electricityMixMode);
  const isEmbedded = useSelector(state => state.application.isEmbedded);
  const location = useLocation();

  const handleMapLoaded = useMemo(
    () => () => {
      // Map loading is finished, lower the overlay shield
      dispatchApplication('isLoadingMap', false);
    
      if (thirdPartyServices._ga) {
        thirdPartyServices._ga.timingMark('map_loaded');
      }
    },
    [],
  );

  const handleSeaClick = useMemo(
    () => () => {
      navigateTo({ pathname: '/map', search: location.search });
    },
    [location],
  );

  const handleZoneClick = useMemo(
    () => (zoneId) => {
      dispatchApplication('isLeftPanelCollapsed', false);
      navigateTo({ pathname: `/zone/${zoneId}`, search: location.search });
      thirdPartyServices.trackWithCurrentApplicationState('countryClick');
    },
    [location],
  );

  const handleZoneMouseMove = useMemo(
    () => (zoneData, zoneId, x, y) => {
      dispatchApplication(
        'co2ColorbarValue',
        electricityMixMode === 'consumption'
          ? zoneData.co2intensity
          : zoneData.co2intensityProduction
      );
      dispatch({
        type: 'SHOW_TOOLTIP',
        payload: {
          data: zoneData,
          displayMode: MAP_COUNTRY_TOOLTIP_KEY,
          position: { x, y },
        },
      });
    },
    [electricityMixMode],
  );

  const handleZoneMouseOut = useMemo(
    () => () => {
      dispatchApplication('co2ColorbarValue', null);
      dispatch({ type: 'HIDE_TOOLTIP' });
    },
    [],
  );

  return (
    <Map
      scrollZoom={!isEmbedded}
      onMapLoaded={handleMapLoaded}
      onSeaClick={handleSeaClick}
      onZoneClick={handleZoneClick}
      onZoneMouseMove={handleZoneMouseMove}
      onZoneMouseOut={handleZoneMouseOut}
    />
  );
};
