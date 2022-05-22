import React from 'react';
import { arc } from 'd3-shape';
import { useSpring, animated } from '@react-spring/web';

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

    const spring = useSpring({
      percentage: Number.isFinite(percentage) ? percentageFill(percentage) : 0,
    });

    return (
      <div
        onClick={(e) => onClick && onClick(e.clientX, e.clientY)}
        onMouseOver={() => onMouseOver && onMouseOver()}
        onMouseOut={() => onMouseOut && onMouseOut()}
        onMouseMove={(e) => onMouseMove && onMouseMove(e.clientX, e.clientY)}
      >
        <svg style={{ pointerEvents: 'none' }} width={radius * 2} height={radius * 2}>
          <g transform={`translate(${radius},${radius})`} className="circular-gauge">
            <path className="background" d={percentageFill(100)} />
            <animated.path className="foreground" d={spring.percentage} />
            <text style={{ textAnchor: 'middle', fontWeight: 'bold', fontSize }} dy="0.4em">
              {Number.isFinite(percentage) ? `${Math.round(percentage)}%` : '?'}
            </text>
          </g>
        </svg>
      </div>
    );
  }
);

export default CircularGauge;
