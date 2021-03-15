import React, { useMemo, useState } from 'react';
import {
  first, last, sortedIndex, isNumber,
} from 'lodash';
import { scaleTime } from 'd3-scale';
import moment from 'moment';

import TimeAxis from './graph/timeaxis';
import { useRefWidthHeightObserver } from '../hooks/viewport';
import { useCurrentNightTimes } from '../hooks/redux';
import { TimeSliderInput } from './TimeSliderInput';

const AXIS_HORIZONTAL_MARGINS = 12;

const getTimeScale = (rangeEnd, datetimes, startTime, endTime) => scaleTime()
  .domain([
    startTime ? moment(startTime).toDate() : first(datetimes),
    endTime ? moment(endTime).toDate() : last(datetimes),
  ])
  .range([0, rangeEnd]);

const createChangeAndInputHandler = (
  datetimes,
  onChange,
  setAnchoredTimeIndex,
) => (ev) => {
  const value = parseInt(ev.target.value, 10);
  let index = sortedIndex(
    datetimes.map(t => t.valueOf()),
    value,
  );
  // If the slider is past the last datetime, we set index to null in order to use the scale end time.
  if (index >= datetimes.length) {
    index = null;
  }
  setAnchoredTimeIndex(index);
  if (onChange) {
    onChange(index);
  }
};

const TimeSlider = ({
  className,
  onChange,
  selectedTimeIndex,
  datetimes,
  startTime,
  endTime,
}) => {
  const { ref, width } = useRefWidthHeightObserver(2 * AXIS_HORIZONTAL_MARGINS);
  // const { ref: ref2 } = useRefWidthHeightObserver(2 * AXIS_HORIZONTAL_MARGINS);

  const [anchoredTimeIndex, setAnchoredTimeIndex] = useState(null);
  const nightTimes = useCurrentNightTimes();

  const timeScale = useMemo(
    () => getTimeScale(width, datetimes, startTime, endTime),
    [width, datetimes, startTime, endTime],
  );

  const startTimeValue = timeScale.domain()[0].valueOf();
  const endTimeValue = timeScale.domain()[1].valueOf();

  // Creating a scale for the night-time background gradients
  const gradientScale = useMemo(
    () => getTimeScale(100, nightTimes, startTimeValue, endTimeValue),
    [nightTimes, timeScale],
  );

  const nightTimeSets = nightTimes.flatMap(([start, end]) => [
    {
      start: Math.max(0, gradientScale(start)),
      end: Math.min(100, gradientScale(end)),
    },
  ]);

  const handleChangeAndInput = useMemo(
    () => createChangeAndInputHandler(datetimes, onChange, setAnchoredTimeIndex),
    [datetimes, onChange, setAnchoredTimeIndex],
  );

  if (!datetimes || datetimes.length === 0) return null;

  const selectedTimeValue = isNumber(selectedTimeIndex)
    ? datetimes[selectedTimeIndex].valueOf()
    : null;
  const anchoredTimeValue = isNumber(anchoredTimeIndex)
    ? datetimes[anchoredTimeIndex].valueOf()
    : null;

  return (
    <div className={className}>
      <TimeSliderInput
        onChange={handleChangeAndInput}
        value={selectedTimeValue || anchoredTimeValue || endTimeValue}
        nightTimeSets={nightTimeSets}
        min={startTimeValue}
        max={endTimeValue}
      />
      <svg className="time-slider-axis-container" ref={ref}>
        <TimeAxis
          scale={timeScale}
          transform={`translate(${AXIS_HORIZONTAL_MARGINS}, 0)`}
          className="time-slider-axis"
        />
      </svg>
    </div>
  );
};

export default TimeSlider;
