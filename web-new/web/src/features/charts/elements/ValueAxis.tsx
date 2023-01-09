/* eslint-disable react/display-name */
import React from 'react';

const ValueAxis = React.memo(({ scale, label, width, height }: any) => {
  const [y1, y2] = scale.range();
  return (
    <g
      transform={`translate(${width - 1} -1)`}
      fill="none"
      fontSize="10"
      fontFamily="sans-serif"
      textAnchor="start"
      className="opacity-50"
      strokeWidth={0.5}
      style={{ pointerEvents: 'none' }}
    >
      {label && (
        <text
          textAnchor="middle"
          stroke="gray"
          strokeWidth={0.5}
          fontSize="0.6rem"
          fill="gray"
          transform={`translate(38, ${height / 2}) rotate(-90)`}
        >
          {label}
        </text>
      )}
      <path
        className="domain"
        stroke="currentColor"
        d={`M6,${y1 + 0.5}H0.5V${y2 + 0.5}H6`}
      />
      {scale.ticks(5).map((v: any) => (
        <g
          key={`valueaxis-tick-${v}`}
          className="tick"
          opacity={1}
          transform={`translate(0,${scale(v)})`}
        >
          <line stroke="currentColor" x2="6" />
          <text fill="currentColor" x="6" y="3" dx="0.32em">
            {v}
          </text>
        </g>
      ))}
    </g>
  );
});

export default ValueAxis;
