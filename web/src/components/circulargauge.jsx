import React from 'react';
import { Motion, spring } from 'react-motion';
import { arc } from 'd3-shape';
import styled from 'styled-components';

/*
  Note: Motion has a bug https://github.com/chenglou/react-motion/issues/567
  that causes a Warning: Can't perform a React state update on an unmounted component
  including Motion.startAnimationIfNecessary in the stack trace.
*/

const CircularGaugeGroup = styled.g`
  .background {
    fill: var(--light-gray);
  }

  .foreground {
    fill: var(--light-blue);
  }
`;

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
        role="tooltip"
        aria-hidden="true"
        onClick={() => onClick && onClick()}
        onMouseOver={() => onMouseOver && onMouseOver()}
        onFocus={() => onMouseOver && onMouseOver()}
        onMouseOut={() => onMouseOut && onMouseOut()}
        onBlur={() => onMouseOut && onMouseOut()}
        onMouseMove={(e) => onMouseMove && onMouseMove(e.clientX, e.clientY)}
      >
        <svg style={{ pointerEvents: 'none' }} width={radius * 2} height={radius * 2}>
          <g transform={`translate(${radius},${radius})`}>
            <CircularGaugeGroup>
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
            </CircularGaugeGroup>
          </g>
        </svg>
      </div>
    );
  }
);

export default CircularGauge;
