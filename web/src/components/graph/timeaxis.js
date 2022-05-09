import React from 'react';
import moment from 'moment';
import { range } from 'lodash';

const TOTAL_TICK_COUNT = 25; // total number of ticks to be displayed
const TICK_VALUE_FREQUENCY = 6; // Frequency at which values are displayed for a tick

const renderTickValue = (v, idx, displayLive) => {
  const shouldDisplayLive = idx === 24 && displayLive; // TODO: change this for other aggregations

  if (shouldDisplayLive) {
    return (
      <g>
        <circle cx="-1em" cy="1.15em" r="2" fill="red" />
        <text fill="#DE3054" y="9" x="5" dy="0.71em" fontWeight="bold">
          LIVE
        </text>
      </g>
    );
  } else {
    return (
      <text fill="currentColor" y="9" x="5" dy="0.71em">
        {moment(v).format('LT')}
      </text>
    );
  }
};

const roundUp = (number, base) => Math.ceil(number / base) * base;

// Return `count` timestamp values uniformly distributed within the scale
// domain, including both ends, rounded up to 15 minutes precision.
const getTicksValuesFromTimeScale = (scale, count) => {
  const startTime = scale.domain()[0].valueOf();
  const endTime = scale.domain()[1].valueOf();

  const precision = moment.duration(60, 'minutes').valueOf();
  const step = (endTime - startTime) / (count - 1);

  return range(count).map((ind) =>
    moment(ind === count - 1 ? endTime : roundUp(startTime + ind * step, precision)).toDate()
  );
};

const renderTick = (scale, val, idx, displayLive) => {
  const shouldShowValue = idx % TICK_VALUE_FREQUENCY === 0;
  return (
    <g key={`tick-${val}`} className="tick" opacity={1} transform={`translate(${scale(val)},0)`}>
      <line stroke="currentColor" y2="6" opacity={shouldShowValue ? 0.5 : 0.2} />
      {shouldShowValue && renderTickValue(val, idx, displayLive)}
    </g>
  );
};

const TimeAxis = React.memo(({ className, scale, transform, displayLive }) => {
  const [x1, x2] = scale.range();
  return (
    <g
      className={className}
      transform={transform}
      fill="none"
      textAnchor="middle"
      style={{ pointerEvents: 'none' }}
    >
      <path className="domain" stroke="currentColor" d={`M${x1 + 0.5},6V0.5H${x2 + 0.5}V6`} />
      {getTicksValuesFromTimeScale(scale, TOTAL_TICK_COUNT).map((v, idx) =>
        renderTick(scale, v, idx, displayLive)
      )}
    </g>
  );
});

export default TimeAxis;
