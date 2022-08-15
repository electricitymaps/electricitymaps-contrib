import React from 'react';

const ValueAxis = React.memo(({ scale, label, width, height }) => {
  const [y1, y2] = scale.range();
  return (
    <g
      className="y axis"
      transform={`translate(${width - 1} -1)`}
      fill="none"
      fontSize="10"
      fontFamily="sans-serif"
      textAnchor="start"
      style={{ pointerEvents: 'none' }}
    >
      {label && (
        <text className="label" textAnchor="middle" transform={`translate(37, ${height / 2}) rotate(-90)`}>
          {label}
        </text>
      )}
      <path className="domain" stroke="currentColor" d={`M6,${y1 + 0.5}H0.5V${y2 + 0.5}H6`} />
      {scale.ticks(5).map((v) => (
        <g key={`valueaxis-tick-${v}`} className="tick" opacity={1} transform={`translate(0,${scale(v)})`}>
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
