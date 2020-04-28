import React, { useState, useMemo } from 'react';
import { useSelector } from 'react-redux';
import ReactMapGL from 'react-map-gl';

import { useCo2ColorScale, useTheme } from '../hooks/theme';
import { useZoneGeometries } from '../hooks/map';

const Map = () => {
  const theme = useTheme();
  const co2Scale = useCo2ColorScale();
  const zoneGeometries = useZoneGeometries();

  const mapStyle = useMemo(
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

  const [viewport, setViewport] = useState({
    latitude: 50,
    longitude: 0,
    zoom: 3,
  });

  // TODO: Detect WebGL support.
  // TODO: Add navigation control.
  // TODO: Put viewport state in Redux.
  // TODO: Add click events
  // TODO: Add hover events
  // TODO: Re-enable layers.

  return (
    <ReactMapGL
      width="100vw"
      height="100vh"
      latitude={viewport.latitude}
      longitude={viewport.longitude}
      zoom={viewport.zoom}
      dragRotate={false}
      touchRotate={false}
      mapStyle={mapStyle}
      onViewportChange={setViewport}
    />
  );
};

export default Map;
