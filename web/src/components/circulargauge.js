import React from 'react';
import { Motion, spring } from 'react-motion';
import { isFinite } from 'lodash';
import { arc } from 'd3-shape';

/* eslint-disable jsx-a11y/mouse-events-have-key-events */
// TODO: re-enable rule

const CircularGauge = React.memo(({
  fontSize = '1rem',
  onClick,
  onMouseMove,
  onMouseOut,
  onMouseOver,
  percentage = 0,
  radius = 32,
  thickness = 6,
}) => {
  const percentageFill = p => arc()
    .startAngle(0)
    .outerRadius(radius)
    .innerRadius(radius - thickness)
    .endAngle((p / 100) * 2 * Math.PI)();

  return (
    <div
      onClick={e => onClick && onClick(e.clientX, e.clientY)}
      onMouseOver={() => onMouseOver && onMouseOver()}
      onMouseOut={() => onMouseOut && onMouseOut()}
      onMouseMove={e => onMouseMove && onMouseMove(e.clientX, e.clientY)}
    >
      <svg style={{ pointerEvents: 'none' }} width={radius * 2} height={radius * 2}>
        <g transform={`translate(${radius},${radius})`}>
          <g className="circular-gauge">
            <path className="background" d={percentageFill(100)} />
            <Motion
              defaultStyle={{ percentage: 0 }}
              style={{ percentage: spring(isFinite(percentage) ? percentage : 0) }}
            >
              {interpolated => (
                <path className="foreground" d={percentageFill(interpolated.percentage)} />
              )}
            </Motion>
            <text style={{ textAnchor: 'middle', fontWeight: 'bold', fontSize }} dy="0.4em">
              {isFinite(percentage) ? `${Math.round(percentage)}%` : '?'}
            </text>
          </g>
        </g>
      </svg>
    </div>
  );
});

export default CircularGauge;
