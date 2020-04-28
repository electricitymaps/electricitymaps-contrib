import React, { useState, useMemo } from 'react';
import { useSelector } from 'react-redux';
import ReactMapGL from 'react-map-gl';
import { keys, values } from 'lodash';

import { themes } from '../helpers/themes';
import { getCo2Scale } from '../helpers/scales';

const Map = () => {
  const brightModeEnabled = useSelector(state => state.application.brightModeEnabled);
  // TODO: Move to a hook.
  const theme = useMemo(
    () => (brightModeEnabled ? themes.bright : themes.dark),
    [brightModeEnabled],
  );
  // TODO: Move to a hook.
  const colorBlindModeEnabled = useSelector(state => state.application.colorBlindModeEnabled);
  const co2Scale = useMemo(
    () => getCo2Scale(colorBlindModeEnabled),
    [colorBlindModeEnabled],
  );

  const zones = useSelector(state => state.data.grid.zones);
  const electricityMixMode = useSelector(state => state.application.electricityMixMode);

  // TODO: Move to a hook.
  const data = useMemo(
    () => (
      electricityMixMode === 'consumption'
        ? values(zones || {})
        : values(zones || {})
          .map(d => ({ ...d, co2intensity: d.co2intensityProduction }))
    ),
    [electricityMixMode, zones],
  );

  // TODO: Move to a hook.
  const zoneGeometries = useMemo(
    () => {
      const clickable = [];
      const nonClickable = [];

      keys(data).forEach((zoneId) => {
        const { geometry } = data[zoneId];
        // Remove empty geometries
        // TODO: Make this operation immutable.
        geometry.coordinates = geometry.coordinates.filter(d => d.length !== 0);
        const feature = {
          type: 'Feature',
          geometry,
          properties: {
            zoneId,
            co2intensity: data[zoneId].co2intensity,
          },
        };
        if (data[zoneId].isClickable === undefined || data[zoneId].isClickable === true) {
          clickable.push(feature);
        } else {
          nonClickable.push(feature);
        }
      });

      return { clickable, nonClickable };
    },
    [data],
  );

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
