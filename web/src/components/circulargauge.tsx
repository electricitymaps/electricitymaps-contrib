import React from 'react';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'reac... Remove this comment to see the full error message
import { Motion, spring } from 'react-motion';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'd3-s... Remove this comment to see the full error message
import { arc } from 'd3-shape';

/*
  Note: Motion has a bug https://github.com/chenglou/react-motion/issues/567
  that causes a Warning: Can't perform a React state update on an unmounted component
  including Motion.startAnimationIfNecessary in the stack trace.
*/

const CircularGauge = React.memo(
  ({
    // @ts-expect-error TS(2339): Property 'fontSize' does not exist on type '{}'.
    fontSize = '1rem',
    // @ts-expect-error TS(2339): Property 'onClick' does not exist on type '{}'.
    onClick,
    // @ts-expect-error TS(2339): Property 'onMouseMove' does not exist on type '{}'... Remove this comment to see the full error message
    onMouseMove,
    // @ts-expect-error TS(2339): Property 'onMouseOut' does not exist on type '{}'.
    onMouseOut,
    // @ts-expect-error TS(2339): Property 'onMouseOver' does not exist on type '{}'... Remove this comment to see the full error message
    onMouseOver,
    // @ts-expect-error TS(2339): Property 'percentage' does not exist on type '{}'.
    percentage = 0,
    // @ts-expect-error TS(2339): Property 'radius' does not exist on type '{}'.
    radius = 32,
    // @ts-expect-error TS(2339): Property 'thickness' does not exist on type '{}'.
    thickness = 6,
  }) => {
    const percentageFill = (p: any) =>
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
            <g className="circular-gauge">
              <path className="background" d={percentageFill(100)} />
              <Motion
                defaultStyle={{ percentage: 0 }}
                style={{ percentage: spring(Number.isFinite(percentage) ? percentage : 0) }}
              >
                {(interpolated: any) => <path className="foreground" d={percentageFill(interpolated.percentage)} />}
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
