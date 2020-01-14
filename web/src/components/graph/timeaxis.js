import React from 'react';
import moment from 'moment';

import Axis from './axis';

const TimeAxis = React.memo(({ scale, height }) => {
  const renderLine = range => `M${range[0] + 0.5},6V0.5H${range[1] + 0.5}V6`;
  const renderTick = v => (
    <g key={`tick-${v}`} className="tick" opacity={1} transform={`translate(${scale(v)},0)`}>
      <line stroke="currentColor" y2="6" />
      <text fill="currentColor" y="9" dy="0.71em">{moment(v).format('LT')}</text>
    </g>
  );

  return (
    <Axis
      className="x axis"
      scale={scale}
      renderLine={renderLine}
      renderTick={renderTick}
      textAnchor="middle"
      transform={`translate(-1 ${height - 1})`}
    />
  );
});

export default TimeAxis;
