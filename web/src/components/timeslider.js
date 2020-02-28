import React, {
  useRef,
  useMemo,
  useState,
  useEffect,
} from 'react';
import {
  first,
  last,
  sortedIndex,
  range,
  isNumber,
} from 'lodash';
import { scaleTime } from 'd3-scale';
import moment from 'moment';

import { __ } from '../helpers/translation';
import TimeAxis from './graph/timeaxis';

const NUMBER_OF_TICKS = 5;
const AXIS_MARGIN_LEFT = 2;

const getTimeScale = (containerWidth, datetimes, startTime, endTime) => scaleTime()
  .domain([
    startTime ? moment(startTime).toDate() : first(datetimes),
    endTime ? moment(endTime).toDate() : last(datetimes),
  ])
  .range([0, containerWidth]);

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

  const selectedTimeValue = isNumber(selectedTimeIndex) ? timestamps[selectedTimeIndex].valueOf() : null;
  const anchoredTimeValue = isNumber(anchoredTimeIndex) ? timestamps[anchoredTimeIndex].valueOf() : null;
  const endTimeValue = timeScale.domain()[1].valueOf();

  return (
    <div className={className}>
      <input
        type="range"
        className="time-slider-input"
        onChange={handleChangeAndInput}
        onInput={handleChangeAndInput}
        value={selectedTimeValue || anchoredTimeValue || endTimeValue}
        min={timeScale.domain()[0].valueOf()}
        max={timeScale.domain()[1].valueOf()}
      />
      <svg className="time-slider-axis-container" ref={ref}>
        <TimeAxis
          scale={timeScale}
          transform={`translate(${AXIS_MARGIN_LEFT}, 0)`}
          className="time-slider-axis"
        />
      </svg>
    </div>
  );
};

export default TimeSlider;
