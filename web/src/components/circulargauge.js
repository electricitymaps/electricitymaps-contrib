/* eslint-disable jsx-a11y/mouse-events-have-key-events */
// TODO: re-enable rule

import React from 'react';
import { isNumber } from 'lodash';
import { arc as d3Arc } from 'd3-shape';
import { useSpring } from 'react-spring';

const CircularGauge = ({
  fontSize = '1rem',
  lineWidth = 6,
  onMouseMove,
  onMouseOut,
  onMouseOver,
  percentage,
  radius = 32,
}) => {
  const arc = d3Arc()
    .startAngle(0)
    .innerRadius(radius - lineWidth)
    .outerRadius(radius);

  const props = useSpring({ animatedPercentage: isNumber(percentage) ? percentage : 0, from: { animatedPercentage: 0 } });
  console.log(props.animatedPercentage.value);

  // const i = d3.interpolate(
  //   (this.state.prevPercentage / 100) * 2 * Math.PI,
  //   (percentage / 100) * 2 * Math.PI
  // );
  // d3.select(this.foregroundRef.current)
  //   .transition()
  //   .duration(500)
  //   .attrTween(
  //     'd',
  //     () => t => this.arc.endAngle(i(t))(),
  //   )
  //   .on('end', () => this.setState({ prevPercentage: percentage }));

  return (
    <div
      onMouseOver={() => onMouseOver && onMouseOver()}
      onMouseOut={() => onMouseOut && onMouseOut()}
      onMouseMove={e => onMouseMove && onMouseMove(e.clientX, e.clientY)}
    >
      <svg width={radius * 2} height={radius * 2}>
        <g transform={`translate(${radius},${radius})`}>
          <g className="circular-gauge">
            <path className="background" d={arc.endAngle(2 * Math.PI)()} />
            <path
              className="foreground"
              d={arc.endAngle((props.animatedPercentage.value / 100) * 2 * Math.PI)()}
            />
            <text style={{ textAnchor: 'middle', fontWeight: 'bold', fontSize }} dy="0.4em">
              {isNumber(percentage) ? `${Math.round(percentage)}%` : '?'}
            </text>
          </g>
        </g>
      </svg>
    </div>
  );
};

export default CircularGauge;
