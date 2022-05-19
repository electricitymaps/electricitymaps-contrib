import React from 'react';
import { Motion, spring } from 'react-motion';
import { arc } from 'd3-shape';

/* eslint-disable jsx-a11y/mouse-events-have-key-events */
// TODO: re-enable rule

/*
  Note: Motion has a bug https://github.com/chenglou/react-motion/issues/567
  that causes a Warning: Can't perform a React state update on an unmounted component
  including Motion.startAnimationIfNecessary in the stack trace.
*/

const CircularGauge = React.memo(
  ({
    fontSize = '1rem',
    onClick,
    onMouseMove,
    onMouseOut,
    onMouseOver,
    percentage = 0,
    radius = 32,
    thickness = 6,
  }) => {
    const percentageFill = (p) =>
      arc()
        .startAngle(0)
        .outerRadius(radius)
        .innerRadius(radius - thickness)
        .endAngle((p / 100) * 2 * Math.PI)();

    return (
      <div
        onClick={(e) => onClick && onClick(e.clientX, e.clientY)}
        onMouseOver={() => onMouseOver && onMouseOver()}
        onMouseOut={() => onMouseOut && onMouseOut()}
        onMouseMove={(e) => onMouseMove && onMouseMove(e.clientX, e.clientY)}
      >
        <svg style={{ pointerEvents: 'none' }} width={radius * 2} height={radius * 2}>
          <g transform={`translate(${radius},${radius})`}>
            <g className="circular-gauge">
              <path className="background" d={percentageFill(100)} />
              <Motion
                defaultStyle={{ percentage: 0 }}
                style={{ percentage: spring(Number.isFinite(percentage) ? percentage : 0) }}
              >
                {(interpolated) => <path className="foreground" d={percentageFill(interpolated.percentage)} />}
              </Motion>
              <text style={{ textAnchor: 'middle', fontWeight: 'bold', fontSize }} dy="0.4em">
                {Number.isFinite(percentage) ? `${Math.round(percentage)}%` : '?'}
              </text>
            </g>
          </g>
        </svg>
      </div>
    );
  }
);

export default CircularGauge;
