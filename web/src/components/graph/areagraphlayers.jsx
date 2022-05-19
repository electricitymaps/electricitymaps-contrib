import React from 'react';
import { noop } from '../../helpers/noop';
import { area, curveStepAfter } from 'd3-shape';

import { detectHoveredDatapointIndex } from '../../helpers/graph';

const AreaGraphLayers = React.memo(
  ({ layers, datetimes, timeScale, valueScale, mouseMoveHandler, mouseOutHandler, isMobile, svgNode }) => {
    const [x1, x2] = timeScale.range();
    const [y2, y1] = valueScale.range();
    if (x1 >= x2 || y1 >= y2) {
      return null;
    }

    // Generate layer paths
    const layerArea = area()
      .curve(curveStepAfter)
      .x((d) => timeScale(d.data.datetime))
      .y0((d) => valueScale(d[0]))
      .y1((d) => valueScale(d[1]))
      .defined((d) => Number.isFinite(d[1]));
    // Mouse hover events
    let mouseOutTimeout;
    const handleLayerMouseMove = (ev, layerIndex) => {
      if (mouseOutTimeout) {
        clearTimeout(mouseOutTimeout);
        mouseOutTimeout = undefined;
      }
      const timeIndex = detectHoveredDatapointIndex(ev, datetimes, timeScale, svgNode);
      if (mouseMoveHandler) {
        mouseMoveHandler(timeIndex, layerIndex);
      }
    };
    const handleLayerMouseOut = () => {
      if (mouseOutHandler) {
        mouseOutHandler();
      }
    };

    return (
      <g>
        {layers.map((layer, ind) => {
          const isGradient = typeof layer.fill === 'function';
          const gradientId = `areagraph-gradient-${layer.key}`;
          return (
            <React.Fragment key={layer.key}>
              <path
                className={`area layer ${layer.key}`}
                style={{ cursor: 'pointer' }}
                stroke={layer.stroke}
                fill={isGradient ? `url(#${gradientId})` : layer.fill}
                d={layerArea(layer.datapoints)}
                /* Support only click events in mobile mode, otherwise react to mouse hovers */
                onClick={isMobile ? (ev) => handleLayerMouseMove(ev, ind) : noop}
                onFocus={!isMobile ? (ev) => handleLayerMouseMove(ev, ind) : noop}
                onMouseOver={!isMobile ? (ev) => handleLayerMouseMove(ev, ind) : noop}
                onMouseMove={!isMobile ? (ev) => handleLayerMouseMove(ev, ind) : noop}
                onMouseOut={handleLayerMouseOut}
                onBlur={handleLayerMouseOut}
              />
              {isGradient && (
                <linearGradient id={gradientId} gradientUnits="userSpaceOnUse" x1={x1} x2={x2}>
                  {layer.datapoints.map((d) => (
                    <stop
                      key={d.data.datetime}
                      offset={`${((timeScale(d.data.datetime) - x1) / (x2 - x1)) * 100.0}%`}
                      stopColor={layer.fill(d)}
                    />
                  ))}
                </linearGradient>
              )}
            </React.Fragment>
          );
        })}
      </g>
    );
  }
);

export default AreaGraphLayers;
