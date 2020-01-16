import React from 'react';
import { noop } from 'lodash';
import { area } from 'd3-shape';

import { detectHoveredDatapointIndex } from '../../helpers/graph';

const AreaGraphLayers = React.memo(({
  layers,
  fillSelector,
  timeScale,
  valueScale,
  mouseMoveHandler,
  mouseOutHandler,
  layerMouseMoveHandler,
  layerMouseOutHandler,
  isMobile,
  svgRef,
}) => {
  if (!layers || !layers[0]) return null;

  const datetimes = layers[0].data.map(d => d.data.datetime);
  const layerArea = area()
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
    const timeIndex = detectHoveredDatapointIndex(ev, datetimes, timeScale, svgRef);
    if (layerMouseMoveHandler) {
      layerMouseMoveHandler(timeIndex, layerIndex, layer, ev, svgRef);
    }
    if (mouseMoveHandler) {
      mouseMoveHandler(timeIndex);
    }
  };
  const handleLayerMouseOut = () => {
    mouseOutTimeout = setTimeout(() => {
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
          fill={fillSelector(ind)}
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
