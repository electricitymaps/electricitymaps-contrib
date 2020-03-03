import React from 'react';
import moment from 'moment';

const TimeAxis = React.memo(({ scale, height }) => {
  const [x1, x2] = scale.range();
  return (
    <g
      className="x axis"
      transform={`translate(-1 ${height - 1})`}
      fill="none"
      fontSize="10"
      fontFamily="sans-serif"
      textAnchor="middle"
      style={{ pointerEvents: 'none' }}
    >
      <path className="domain" stroke="currentColor" d={`M${x1 + 0.5},6V0.5H${x2 + 0.5}V6`} />
      {scale.ticks(5).map(v => (
        <g key={`tick-${v}`} className="tick" opacity={1} transform={`translate(${scale(v)},0)`}>
          <line stroke="currentColor" y2="6" />
          <text fill="currentColor" y="9" dy="0.71em">{moment(v).format('LT')}</text>
        </g>
      ))}
    </g>
  );
});

export default TimeAxis;
