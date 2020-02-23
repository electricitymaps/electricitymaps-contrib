import React from 'react';
import { noop } from 'lodash';
import { area } from 'd3-shape';

import { detectHoveredDatapointIndex } from '../../helpers/graph';

const AreaGraphLayers = React.memo(({
  layers,
  datetimes,
  timeScale,
  valueScale,
  mouseMoveHandler,
  mouseOutHandler,
  layerMouseMoveHandler,
  layerMouseOutHandler,
  isMobile,
  svgRef,
}) => {
  const [x1, x2] = timeScale.range();
  if (x1 >= x2) return null;

  // Generate layer paths
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
        <React.Fragment>
          <path
            key={layer.key}
            className={`area layer ${layer.key}`}
            style={{ cursor: 'pointer' }}
            fill={layer.fill}
            d={layerArea(layer.datapoints)}
            /* Support only click events in mobile mode, otherwise react to mouse hovers */
            onClick={isMobile ? (ev => handleLayerMouseMove(ev, layer, ind)) : noop}
            onFocus={!isMobile ? (ev => handleLayerMouseMove(ev, layer, ind)) : noop}
            onMouseOver={!isMobile ? (ev => handleLayerMouseMove(ev, layer, ind)) : noop}
            onMouseMove={!isMobile ? (ev => handleLayerMouseMove(ev, layer, ind)) : noop}
            onMouseOut={handleLayerMouseOut}
            onBlur={handleLayerMouseOut}
          />
          {layer.gradient && (
            <linearGradient
              key={layer.gradient.key}
              id={layer.gradient.key}
              gradientUnits="userSpaceOnUse"
              x1={x1}
              x2={x2}
            >
              {layer.datapoints.map(d => (
                <stop
                  key={d.data.datetime}
                  offset={`${(timeScale(d.data.datetime) - x1) / (x2 - x1) * 100.0}%`}
                  stopColor={layer.gradient.datapointFill(d)}
                />
              ))}
            </linearGradient>
          )}
        </React.Fragment>
      ))}
    </g>
  );
});

export default AreaGraphLayers;
