import React from 'react';
import { noop } from 'lodash';

import { detectHoveredDatapointIndex } from '../../helpers/graph';

const d3 = Object.assign(
  {},
  require('d3-shape'),
);

const AreaGraphLayers = React.memo(({
  layers,
  fillColor,
  timeScale,
  valueScale,
  setSelectedLayerIndex,
  mouseMoveHandler,
  mouseOutHandler,
  layerMouseMoveHandler,
  layerMouseOutHandler,
  isMobile,
  svgRef,
}) => {
  if (!layers || !layers[0]) return null;

  const datetimes = layers[0].data.map(d => d.data.datetime);
  const layerArea = d3.area()
    .x(d => timeScale(d.data.datetime))
    .y0(d => valueScale(d[0]))
    .y1(d => valueScale(d[1]))
    .defined(d => Number.isFinite(d[1]));

  // Mouse hover events
  let mouseOutTimeout;
  const handleLayerMouseMove = (ev, layer, layerIndex) => {
    if (mouseOutTimeout) {
      clearTimeout(mouseOutTimeout);
      mouseOutTimeout = undefined;
    }
    setSelectedLayerIndex(layerIndex);
    const timeIndex = detectHoveredDatapointIndex(ev, datetimes, timeScale, svgRef);
    if (layerMouseMoveHandler) {
      // If in mobile mode, put the tooltip to the top of the screen for
      // readability, otherwise float it depending on the cursor position.
      const position = !isMobile
        ? { x: ev.clientX - 7, y: svgRef.current.getBoundingClientRect().top - 7 }
        : { x: 0, y: 0 };
      layerMouseMoveHandler(layer.key, position, layer.data[timeIndex].data._countryData);
    }
    if (mouseMoveHandler) {
      mouseMoveHandler(layer.data[timeIndex].data._countryData, timeIndex);
    }
  };
  const handleLayerMouseOut = () => {
    mouseOutTimeout = setTimeout(() => {
      setSelectedLayerIndex(undefined);
      if (mouseOutHandler) {
        mouseOutHandler();
      }
      if (layerMouseOutHandler) {
        layerMouseOutHandler();
      }
    }, 50);
  };

  return (
    <g>
      {layers.map((layer, ind) => (
        <path
          key={layer.key}
          className={`area layer ${layer.key}`}
          style={{ cursor: 'pointer' }}
          fill={fillColor(ind)}
          d={layerArea(layer.data)}
          /* Support only click events in mobile mode, otherwise react to mouse hovers */
          onClick={isMobile ? (ev => handleLayerMouseMove(ev, layer, ind)) : noop}
          onFocus={!isMobile ? (ev => handleLayerMouseMove(ev, layer, ind)) : noop}
          onMouseOver={!isMobile ? (ev => handleLayerMouseMove(ev, layer, ind)) : noop}
          onMouseMove={!isMobile ? (ev => handleLayerMouseMove(ev, layer, ind)) : noop}
          onMouseOut={handleLayerMouseOut}
          onBlur={handleLayerMouseOut}
        />
      ))}
    </g>
  );
});

export default AreaGraphLayers;
