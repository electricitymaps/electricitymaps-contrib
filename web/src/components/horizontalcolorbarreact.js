import React, { useRef, useState } from 'react';
import { range, isFinite } from 'lodash';
import { scaleLinear } from 'd3-scale';
import { extent } from 'd3-array';

import { getCo2Scale } from '../helpers/scales';
import { useWidthObserver, useHeightObserver } from '../effects';

const PADDING_X = 13; // Inner padding allow place for the axis text
const PADDING_Y = 10; // Inner padding allow place for the axis text

const spreadOverDomain = (scale, count) => {
  const [x1, x2] = extent(scale.domain());
  return range(count).map(v => x1 + (x2 - x1) * v / (count - 1));
};

const HorizontalColorbar = ({ colorScale, currentMarker, id, markerColor }) => {
  const ref = useRef(null);
  const width = useWidthObserver(ref, 2 * PADDING_X);
  const height = useHeightObserver(ref, 2 * PADDING_Y);

  const linearScale = scaleLinear()
    .domain(extent(colorScale.domain()))
    .range([0, width]);

  // const deltaOriginal = width - scale.range().length;
  
  return (
    <svg className="colorbar" ref={ref}>
      <g transform={`translate(${PADDING_X},0)`}>
        <linearGradient id={`${id}-gradient`} x2="100%">
          {spreadOverDomain(colorScale, 10).map((value, index) => (
            <stop offset={index / 9} stopColor={colorScale(value)} />
          ))}
        </linearGradient>
        <rect
          className="gradient"
          fill={`url(#${id}-gradient)`}
          width={width}
          height={height}
        />
        {isFinite(currentMarker) && (
          <line
            className="marker"
            stroke={markerColor}
            strokeWidth="2"
            x1={linearScale(currentMarker)}
            x2={linearScale(currentMarker)}
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
          {spreadOverDomain(linearScale, 3).map(t => (
            <g key={`tick-${t}`} className="tick" transform={`translate(${linearScale(t)},0)`}>
              <text fill="currentColor" y="8" dy="0.81em">{t}</text>
            </g>
          ))}
        </g>
      </g>
    </svg>
  )
};

export default HorizontalColorbar;
