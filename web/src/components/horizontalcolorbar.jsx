import React from 'react';
import { scaleLinear } from 'd3-scale';
import { extent } from 'd3-array';

import styled from 'styled-components';
import { useRefWidthHeightObserver } from '../hooks/viewport';

const PADDING_X = 13;
const PADDING_Y = 10;

const Wrapper = styled.svg`
  width: 100%;
  height: 30px;
  /* This will make sure children are relative to 1em */
  font-size: 1rem;

  .tick {
    text {
      fill: #000000;
    }
    line {
      stroke: none;
    }
  }

  rect.border {
    stroke: none;
  }
`;

const spreadOverDomain = (scale, count) => {
  const [x1, x2] = extent(scale.domain());
  return [...Array(count).keys()].map((v) => x1 + ((x2 - x1) * v) / (count - 1));
};

const HorizontalColorbar = ({ colorScale, currentValue, id, markerColor, ticksCount = 5 }) => {
  const { ref, width, height } = useRefWidthHeightObserver(2 * PADDING_X, 2 * PADDING_Y);

  const linearScale = scaleLinear().domain(extent(colorScale.domain())).range([0, width]);

  // Render an empty SVG if the dimensions are not positive
  if (width <= 0 || height <= 0) {
    return <Wrapper ref={ref} />;
  }

  return (
    <Wrapper ref={ref}>
      <g transform={`translate(${PADDING_X},0)`}>
        <linearGradient id={`${id}-gradient`} x2="100%">
          {spreadOverDomain(colorScale, 10).map((value, index) => (
            <stop key={value} offset={index / 9} stopColor={colorScale(value)} />
          ))}
        </linearGradient>
        <rect fill={`url(#${id}-gradient)`} width={width} height={height} />
        {Number.isFinite(currentValue) && (
          <line
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
          {spreadOverDomain(linearScale, ticksCount).map((t) => (
            <g key={`colorbar-tick-${t}`} className="tick" transform={`translate(${linearScale(t)},0)`}>
              <text fill="currentColor" y="8" dy="0.81em">
                {Math.round(t)}
              </text>
            </g>
          ))}
        </g>
      </g>
    </Wrapper>
  );
};

export default HorizontalColorbar;
