import React from 'react';

import Axis from './axis';

const ValueAxis = React.memo(({ scale, label, width }) => {
  const renderLine = range => `M6,${range[0] + 0.5}H0.5V${range[1] + 0.5}H6`;
  const renderTick = v => (
    <g key={`tick-${v}`} className="tick" opacity={1} transform={`translate(0,${scale(v)})`}>
      <line stroke="currentColor" x2="6" />
      <text fill="currentColor" x="6" y="3" dx="0.32em">{v}</text>
    </g>
  );

  return (
    <Axis
      className="y axis"
      label={label}
      scale={scale}
      renderLine={renderLine}
      renderTick={renderTick}
      textAnchor="start"
      transform={`translate(${width - 1} -1)`}
    />
  );
});

export default ValueAxis;
