/* eslint-disable react/display-name */
import { ScaleLinear } from 'd3-scale';
import React from 'react';

interface ValueAxisProps {
  scale: ScaleLinear<number, number, never>;
  width: number;
  formatTick: (value: number) => string | number;
}

function ValueAxis({ scale, width, formatTick }: ValueAxisProps) {
  const [y1, y2] = scale.range();
  return (
    <g
      transform={`translate(${width} 0)`}
      fill="none"
      fontSize="10"
      fontFamily="sans-serif"
      textAnchor="start"
      className="opacity-50"
      style={{ pointerEvents: 'none' }}
    >
      <path
        className="domain"
        stroke="currentColor"
        strokeWidth={0.5}
        d={`M0,${y1}V${y2}H0`}
      />
      {scale.ticks(5).map((v) => (
        <g
          key={`valueaxis-tick-${v}`}
          className="tick"
          transform={`translate(0,${scale(v)})`}
        >
          <line stroke="currentColor" x2="6" opacity={0.5} />
          <text fill="currentColor" x="6" y="3" dx="0.32em">
            {formatTick(v)}
          </text>
        </g>
      ))}
    </g>
  );
}

export default React.memo(ValueAxis);
