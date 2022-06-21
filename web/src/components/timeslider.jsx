import React, { useMemo, useState } from 'react';
import sortedIndex from 'lodash.sortedindex';
import { scaleTime } from 'd3-scale';

import TimeAxis from './graph/timeaxis';
import { useRefWidthHeightObserver } from '../hooks/viewport';

const AXIS_HORIZONTAL_MARGINS = 12;

const getTimeScale = (rangeEnd, datetimes, startTime, endTime) =>
  scaleTime()
    .domain([startTime ? new Date(startTime) : datetimes.at(0), endTime ? new Date(endTime) : datetimes.at(-1)])
    .range([0, rangeEnd])
    .nice(25);

const createChangeAndInputHandler = (datetimes, onChange, setAnchoredTimeIndex) => (ev) => {
  const value = parseInt(ev.target.value, 10);
  let index = sortedIndex(
    datetimes.map((t) => t.valueOf()),
    value
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

const TimeSlider = ({ className, onChange, selectedTimeIndex, datetimes, startTime, endTime }) => {
  const { ref, width } = useRefWidthHeightObserver(2 * AXIS_HORIZONTAL_MARGINS);

  const [anchoredTimeIndex, setAnchoredTimeIndex] = useState(null);

  const timeScale = useMemo(
    () => getTimeScale(width, datetimes, startTime, endTime),
    [width, datetimes, startTime, endTime]
  );

  const startTimeValue = timeScale.domain()[0].valueOf();
  const endTimeValue = timeScale.domain()[1].valueOf();

  const handleChangeAndInput = useMemo(
    () => createChangeAndInputHandler(datetimes, onChange, setAnchoredTimeIndex),
    [datetimes, onChange, setAnchoredTimeIndex]
  );

  if (!datetimes || datetimes.length === 0) {
    return null;
  }

  const selectedTimeValue = typeof selectedTimeIndex === 'number' ? datetimes[selectedTimeIndex].valueOf() : null;
  const anchoredTimeValue = typeof anchoredTimeIndex === 'number' ? datetimes[anchoredTimeIndex].valueOf() : null;

  return (
    <div className={className}>
      <input
        type="range"
        className="time-slider-input"
        onChange={handleChangeAndInput}
        onInput={handleChangeAndInput}
        value={selectedTimeValue || anchoredTimeValue || endTimeValue}
        min={startTimeValue}
        max={endTimeValue}
      />
      <svg className="time-slider-axis-container" ref={ref}>
        <TimeAxis
          scale={timeScale}
          transform={`translate(${AXIS_HORIZONTAL_MARGINS}, 0)`}
          className="time-slider-axis"
          datetimes={datetimes}
        />
      </svg>
    </div>
  );
};

export default TimeSlider;
