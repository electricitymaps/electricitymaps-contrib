import React, {
  useRef,
  useMemo,
  useState,
  useEffect,
} from 'react';
import { first, last, sortedIndex } from 'lodash';
import { scaleTime } from 'd3-scale';
import moment from 'moment';

import { __ } from '../helpers/translation';

const NUMBER_OF_TICKS = 5;
const AXIS_MARGIN_LEFT = 5;

const getTimeScale = (containerWidth, datetimes, startTime, endTime) => scaleTime()
  .domain([
    startTime ? moment(startTime).toDate() : first(datetimes),
    endTime ? moment(endTime).toDate() : last(datetimes),
  ])
  .range([0, containerWidth]);

const sampledTickValues = (data) => {
  const tickValues = [];
  if (data.length >= NUMBER_OF_TICKS) {
    for (let i = 0; i < NUMBER_OF_TICKS; i += 1) {
      const sampleIndex = Math.floor(((data.length - 1) / (NUMBER_OF_TICKS - 1)) * (i));
      tickValues.push(data[sampleIndex]);
    }
  }
  return tickValues;
};

const renderTick = (v, ind) =>
  (ind === NUMBER_OF_TICKS - 1 ? __('country-panel.now') : moment(v).format('LT')); // Localized time, e.g. "8:30 PM"

const TimeSlider = ({
  className,
  onChange,
  selectedTimeIndex,
  timestamps,
  startTime,
  endTime,
}) => {
  const ref = useRef(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const [anchoredTimeIndex, setAnchoredTimeIndex] = useState(null);

  // Container resize hook
  useEffect(() => {
    const updateContainerWidth = () => {
      if (ref.current) {
        setContainerWidth(ref.current.getBoundingClientRect().width - AXIS_MARGIN_LEFT);
      }
    };
    // Initialize width if it's not set yet
    if (!containerWidth) {
      updateContainerWidth();
    }
    // Update container width on every resize
    window.addEventListener('resize', updateContainerWidth);
    return () => {
      window.removeEventListener('resize', updateContainerWidth);
    };
  });

  const timeScale = useMemo(
    () => getTimeScale(containerWidth, timestamps, startTime, endTime),
    [containerWidth, timestamps, startTime, endTime]
  );

  if (!timestamps || timestamps.length === 0) return null;

  const handleChangeAndInput = (ev) => {
    const value = parseInt(ev.target.value, 10);
    const index = sortedIndex(timestamps.map(t => t.valueOf()), value);
    setAnchoredTimeIndex(index);
    if (onChange) {
      onChange(index, timestamps);
    }
  };

  const [x1, x2] = timeScale.range();

  return (
    <div className={className}>
      <input
        type="range"
        className="time-slider-input"
        onChange={handleChangeAndInput}
        onInput={handleChangeAndInput}
        value={timestamps[selectedTimeIndex || anchoredTimeIndex || timestamps.length - 1].valueOf()}
        min={timeScale.domain()[0].valueOf()}
        max={timeScale.domain()[1].valueOf()}
      />
      <svg className="time-slider-axis-container" ref={ref}>
        <g
          className="time-slider-axis"
          transform={`translate(${AXIS_MARGIN_LEFT}, 0)`}
          fill="none"
          fontSize="10"
          fontFamily="sans-serif"
          textAnchor="middle"
          style={{ pointerEvents: 'none' }}
        >
          <path className="domain" stroke="currentColor" d={`M${x1 + 0.5},6V0.5H${x2 + 0.5}V6`} />
          {sampledTickValues(timestamps).map((v, ind) => (
            <g key={`tick-${v}`} className="tick" opacity={1} transform={`translate(${timeScale(v)},0)`}>
              <line stroke="currentColor" y2="0" />
              <text fill="currentColor" y="3" dy="0.71em">{renderTick(v, ind)}</text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
};

export default TimeSlider;
