import React, { useRef, useState } from 'react';
import { range, isFinite } from 'lodash';
import { scaleLinear } from 'd3-scale';
import { extent } from 'd3-array';

import { useWidthObserver, useHeightObserver } from '../hooks/viewport';

const PADDING_X = 13;
const PADDING_Y = 10;

const spreadOverDomain = (scale, count) => {
  const [x1, x2] = extent(scale.domain());
  return range(count).map(v => x1 + (x2 - x1) * v / (count - 1));
};

const HorizontalColorbar = ({
  colorScale,
  currentValue,
  id,
  markerColor,
  ticksCount = 5,
}) => {
  const ref = useRef(null);
  const width = useWidthObserver(ref, 2 * PADDING_X);
  const height = useHeightObserver(ref, 2 * PADDING_Y);

  const className = `${id} colorbar`;
  const linearScale = scaleLinear()
    .domain(extent(colorScale.domain()))
    .range([0, width]);

  // Render an empty SVG if the dimensions are not positive
  if (width <= 0 || height <= 0) {
    return <svg className={className} ref={ref} />;
  }

  return (
    <svg className={className} ref={ref}>
      <g transform={`translate(${PADDING_X},0)`}>
        <linearGradient id={`${id}-gradient`} x2="100%">
          {spreadOverDomain(colorScale, 10).map((value, index) => (
            <stop key={value} offset={index / 9} stopColor={colorScale(value)} />
          ))}
        </linearGradient>
        <rect
          className="gradient"
          fill={`url(#${id}-gradient)`}
          width={width}
          height={height}
        />
        {isFinite(currentValue) && (
          <line
            className="marker"
            stroke={markerColor}
            strokeWidth="2"
            x1={linearScale(currentValue)}
            x2={linearScale(currentValue)}
            y2={height}
          />
        )}
        <rect
          className="border"
          shapeRendering="crispEdges"
          strokeWidth="1"
          fill="none"
          width={width}
          height={height}
        />
        <g
          className="x axis"
          transform={`translate(0,${height})`}
          fill="none"
          fontSize="10"
          fontFamily="sans-serif"
          textAnchor="middle"
        >
          {spreadOverDomain(linearScale, ticksCount).map(t => (
            <g key={`tick-${t}`} className="tick" transform={`translate(${linearScale(t)},0)`}>
              <text fill="currentColor" y="8" dy="0.81em">{Math.round(t)}</text>
            </g>
          ))}
        </g>
      </g>
    </svg>
  );
};

export default HorizontalColorbar;
