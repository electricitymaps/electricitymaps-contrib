import React from 'react';
import Moment from 'moment';
import { extendMoment } from 'moment-range';

import { __ } from '../../helpers/translation';

const moment = extendMoment(Moment);

// If the tick represents a timestamp not more than 15 minutes in the past,
// render it as "Now", otherwise render as localized time, i.e. "8:30 PM".
const renderTickValue = v => (
  moment().diff(moment(v), 'minutes') <= 15
    ? __('country-panel.now')
    // : moment(v).format('LT')
    : moment(v).format('YYYY')
);

const roundUp = (number, base) => Math.ceil(number / base) * base;

// Return `count` timestamp values uniformly distributed within the scale
// domain, including both ends, rounded up to 15 minutes precision.
const getTicksValuesFromTimeScale = (scale, count) => {
  // TODO: USE MOMENT RANGE INSTEAD
  // TODO: Switch to timescale
  const range = moment.range(
    moment(scale.domain()[0]).startOf('year').add(1, 'year'),
    scale.domain()[1]
  );
  return Array.from(range.by('year', { step: 1 }));

  const precision = moment.duration(15, 'minutes').valueOf();
  const step = (endTime - startTime) / (count - 1);

  return range(count).map(ind => (
    moment(ind === count - 1 ? endTime : roundUp(startTime + ind * step, precision)).toDate()
  ));
};

const TimeAxis = React.memo(({ className, scale, transform }) => {
  const [x1, x2] = scale.range();
  return (
    <g
      className={className}
      transform={transform}
      fill="none"
      fontSize="10"
      fontFamily="sans-serif"
      textAnchor="middle"
      style={{ pointerEvents: 'none' }}
    >
      <path className="domain" stroke="currentColor" d={`M${x1 + 0.5},6V0.5H${x2 + 0.5}V6`} />
      {getTicksValuesFromTimeScale(scale, 5).map(v => (
        <g key={`tick-${v}`} className="tick" opacity={1} transform={`translate(${scale(v)},0)`}>
          <line stroke="currentColor" y2="6" />
          <text fill="currentColor" y="9" x="0" dy="0.71em">{renderTickValue(v)}</text>
        </g>
      ))}
    </g>
  );
});

export default TimeAxis;
