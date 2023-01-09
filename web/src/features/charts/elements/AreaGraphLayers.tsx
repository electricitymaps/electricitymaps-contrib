/* eslint-disable unicorn/no-null */
/* eslint-disable react/jsx-handler-names */
import { area, curveStepAfter } from 'd3-shape';
import React from 'react';
import { detectHoveredDatapointIndex, getNextDatetime, noop } from '../graphUtils';
import { AreaGraphElement } from '../types';

interface AreaGraphLayersProps {
  layers: any[];
  datetimes: Date[];
  timeScale: any;
  valueScale: any;
  mouseMoveHandler: any;
  mouseOutHandler: any;
  isMobile: boolean;
  svgNode: any;
}

function AreaGraphLayers({
  layers,
  datetimes,
  timeScale,
  valueScale,
  mouseMoveHandler,
  mouseOutHandler,
  isMobile,
  svgNode,
}: AreaGraphLayersProps) {
  const [x1, x2] = timeScale.range();
  const [y2, y1] = valueScale.range();
  if (x1 >= x2 || y1 >= y2) {
    return null;
  }

  // Generate layer paths
  const layerArea = area()
    // see https://github.com/d3/d3-shape#curveStep
    .curve(curveStepAfter)
    .x((d: any) => timeScale(d.data.datetime))
    .y0((d) => valueScale(d[0]))
    .y1((d) => valueScale(d[1]))
    .defined((d) => Number.isFinite(d[1]));
  // Mouse hover events
  let mouseOutTimeout: string | number | NodeJS.Timeout | undefined;
  const handleLayerMouseMove = (
    event_:
      | React.MouseEvent<SVGPathElement, MouseEvent>
      | React.FocusEvent<SVGPathElement, Element>,
    layerIndex: number
  ) => {
    if (mouseOutTimeout) {
      clearTimeout(mouseOutTimeout);
      mouseOutTimeout = undefined;
    }
    const timeIndex = detectHoveredDatapointIndex(event_, datetimes, timeScale, svgNode);
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
        // A datapoint valid until the next one
        // However, for the last point (or for missing points),
        // we won't have a next point.
        // This affects the way step curves are plotted.
        // Therefore, we copy all datapoints and make sure
        // both a start and an end are present to ensure
        // proper display of missing points
        const datapoints = [
          ...layer.datapoints.map((d: { data: AreaGraphElement }) => [
            {
              ...d,
              data: {
                ...d.data,
                datetime: d.data.datetime,
              },
            },
            {
              ...d,
              data: {
                ...d.data,
                // Here we use a different array which
                // will contain the last datetime.
                datetime: getNextDatetime(datetimes, d.data.datetime),
              },
              isEnd: true,
            },
          ]),
        ].flat();

        return (
          <React.Fragment key={layer.key}>
            <path
              className={layers.length > 1 ? 'sm:hover:opacity-75' : ''}
              style={{ cursor: 'pointer' }}
              stroke={layer.stroke}
              fill={isGradient ? `url(#${gradientId})` : layer.fill}
              d={layerArea(datapoints) || undefined}
              /* Support only click events in mobile mode, otherwise react to mouse hovers */
              onClick={isMobile ? (event_) => handleLayerMouseMove(event_, ind) : noop}
              onFocus={!isMobile ? (event_) => handleLayerMouseMove(event_, ind) : noop}
              onMouseOver={
                !isMobile ? (event_) => handleLayerMouseMove(event_, ind) : noop
              }
              onMouseMove={
                !isMobile ? (event_) => handleLayerMouseMove(event_, ind) : noop
              }
              onMouseOut={handleLayerMouseOut}
              onBlur={handleLayerMouseOut}
            />
            {isGradient && (
              <linearGradient
                id={gradientId}
                gradientUnits="userSpaceOnUse"
                x1={x1}
                x2={x2}
              >
                {datapoints.map((d) => (
                  <stop
                    key={`${d.data.datetime}${d.isEnd}`}
                    offset={`${((timeScale(d.data.datetime) - x1) / (x2 - x1)) * 100}%`}
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

export default React.memo(AreaGraphLayers);
