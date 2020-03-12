/* eslint-disable jsx-a11y/mouse-events-have-key-events */
// TODO: re-enable rule

import React from 'react';

import * as d3Selection from 'd3-selection';
import * as d3Transition from 'd3-transition';
import * as d3Shape from 'd3-shape';
import * as d3Interpolate from 'd3-interpolate';

const d3 = {
  ...d3Selection,
  ...d3Transition,
  ...d3Shape,
  ...d3Interpolate,
};

const DEFAULT_RADIUS = '32';

export default class extends React.PureComponent {
  constructor(props) {
    super(props);

    this.foregroundRef = React.createRef();

    this.state = {
      prevPercentage: 0,
    };

    const radius = this.props.radius || DEFAULT_RADIUS;
    const lineWidth = this.props.lineWidth || '6';

    this.arc = d3.arc()
      .startAngle(0)
      .innerRadius(radius - lineWidth)
      .outerRadius(radius);
  }

  render() {
    const fontSize = this.props.fontSize || '1rem';
    const radius = this.props.radius || DEFAULT_RADIUS;
    const percentage = Number.isNaN(this.props.percentage)
      ? 0
      : (this.props.percentage || 0);

    const i = d3.interpolate(
      (this.state.prevPercentage / 100) * 2 * Math.PI,
      (percentage / 100) * 2 * Math.PI
    );
    d3.select(this.foregroundRef.current)
      .transition()
      .duration(500)
      .attrTween(
        'd',
        () => t => this.arc.endAngle(i(t))(),
      )
      .on('end', () => this.setState({ prevPercentage: percentage }));

    const { onMouseMove, onMouseOut, onMouseOver } = this.props;

    return (
      <div
        onMouseOver={() => onMouseOver && onMouseOver()}
        onMouseOut={() => onMouseOut && onMouseOut()}
        onMouseMove={e => onMouseMove && onMouseMove(e.clientX, e.clientY)}
      >
        <svg width={radius * 2} height={radius * 2}>
          <g transform={`translate(${radius},${radius})`}>
            <g className="circular-gauge">
              <path className="background" d={this.arc.endAngle(2 * Math.PI)()} />
              <path
                className="foreground"
                d={this.arc.endAngle((percentage / 100) * 2 * Math.PI)()}
                ref={this.foregroundRef}
              />
              <text style={{ textAnchor: 'middle', fontWeight: 'bold', fontSize }} dy="0.4em">
                {
                  this.props.percentage != null && !Number.isNaN(this.props.percentage)
                    ? `${Math.round(percentage)}%`
                    : '?'
                }
              </text>
            </g>
          </g>
        </svg>
      </div>
    );
  }
}
