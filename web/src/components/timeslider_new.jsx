import React, { useMemo, useState } from 'react';
import { scaleTime } from 'd3-scale';
import sortedIndex from 'lodash.sortedindex';

import TimeAxis from './graph/timeaxis';
import { useRefWidthHeightObserver } from '../hooks/viewport';
import TimeSliderTooltip from './tooltips/timeslidertooltip';
import TimeControls from './timeControls';
import styled from 'styled-components';
import { useTranslation } from '../helpers/translation';

const AXIS_HORIZONTAL_MARGINS = 12;

const StyledInput = styled.input`
  -webkit-appearance: none;
  width: 100%;
  margin-top: 5px;
  height: 26px;
  background: transparent;
  padding: 0;
  overflow: visible;
  border: none;
  margin: 5px 0;

  &:focus {
    outline: none;
  }

  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    height: 26px;
    width: 26px;
    border-radius: 17px;
    background: #ffffff;
    cursor: pointer;
    margin-top: -8px;
    transition: box-shadow 0.4s;
    box-shadow: 0 0 5px 0 rgba(0, 0, 0, 0.15);
    border: 1px solid lightgray;
    background-position: center center;
    background-size: 12px;
    background-repeat: no-repeat;
    border: none;
    box-shadow: 0.1px 0.1px 6px rgba(0, 0, 0, 0.16);
    // TODO: background-image is set in .scss file

    &:hover {
      box-shadow: 0 0 15px 0 rgba(0, 0, 0, 0.15);
    }
  }

  &::-webkit-slider-runnable-track {
    width: 100%;
    height: 12px;
    border-radius: 4px;
    cursor: pointer;
    background: #f0f0f0;
    background-size: 100% 100%;
    background-repeat: no-repeat;
  }
`;

const getTimeScale = (rangeEnd, datetimes, startTime, endTime) =>
  scaleTime()
    .domain([startTime ? new Date(startTime) : datetimes.at(0), endTime ? new Date(endTime) : datetimes.at(-1)])
    .range([0, rangeEnd])
    .nice(25);

const updateTooltipPosition = (ev, setTooltipPos) => {
  const thumbSize = 25;
  const range = ev.target;
  const ratio = (range.value - range.min) / (range.max - range.min);
  const posY = range.getBoundingClientRect().y;
  const posX = thumbSize / 2 + ratio * range.offsetWidth - ratio * thumbSize;
  setTooltipPos({ x: posX, y: posY });
};

const createChangeAndInputHandler = (datetimes, onChange, setAnchoredTimeIndex, setTooltipPos) => (ev) => {
  const value = parseInt(ev.target.value, 10);
  updateTooltipPosition(ev, setTooltipPos);

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

const TimeSlider = ({
  className,
  onChange,
  selectedTimeIndex,
  datetimes,
  startTime,
  endTime,
  handleTimeAggregationChange,
  selectedTimeAggregate,
}) => {
  const { __ } = useTranslation();
  const { ref, width } = useRefWidthHeightObserver(2 * AXIS_HORIZONTAL_MARGINS);
  const [tooltipPos, setTooltipPos] = useState(null);
  const [anchoredTimeIndex, setAnchoredTimeIndex] = useState(null);

  const timeScale = useMemo(
    () => getTimeScale(width, datetimes, startTime, endTime),
    [width, datetimes, startTime, endTime]
  );

  const startTimeValue = timeScale.domain()[0].valueOf();
  const endTimeValue = timeScale.domain()[1].valueOf();

  const handleChangeAndInput = useMemo(
    () => createChangeAndInputHandler(datetimes, onChange, setAnchoredTimeIndex, setTooltipPos),
    [datetimes, onChange, setAnchoredTimeIndex]
  );

  if (!datetimes || datetimes.length === 0) {
    return null;
  }

  const selectedTimeValue = typeof selectedTimeIndex === 'number' ? datetimes[selectedTimeIndex].valueOf() : null;
  const anchoredTimeValue = typeof anchoredTimeIndex === 'number' ? datetimes[anchoredTimeIndex].valueOf() : null;

  const timeValue = selectedTimeValue || anchoredTimeValue || endTimeValue;

  return (
    <div className={className}>
      <TimeSliderTooltip
        onClose={() => setTooltipPos(null)}
        position={tooltipPos}
        date={new Date(timeValue)}
        disabled // Disabled for now. Part of history feature
      />
      <TimeControls
        date={new Date(timeValue)}
        selectedTimeAggregate={selectedTimeAggregate}
        handleTimeAggregationChange={handleTimeAggregationChange}
      />
      <StyledInput
        className="time-slider-input-new"
        type="range"
        onChange={handleChangeAndInput}
        onInput={onChange}
        value={timeValue}
        min={startTimeValue}
        max={endTimeValue}
      />
      <svg className="time-slider-axis-container" ref={ref}>
        <TimeAxis
          scale={timeScale}
          transform={`translate(${AXIS_HORIZONTAL_MARGINS}, 0)`}
          className="time-slider-axis"
          displayLive
        />
      </svg>
    </div>
  );
};

export default TimeSlider;
