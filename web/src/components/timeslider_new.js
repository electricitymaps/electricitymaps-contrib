import React, { useMemo, useState } from 'react';
import { first, last, sortedIndex, isNumber } from 'lodash';
import { scaleTime } from 'd3-scale';
import moment from 'moment';

import TimeAxis from './graph/timeaxis';
import { useRefWidthHeightObserver } from '../hooks/viewport';
import { useCurrentNightTimes } from '../hooks/redux';
import { TimeSliderInput } from './TimeSliderInput';
import TimeSliderTooltip from './tooltips/timeslidertooltip';
import TimeControls from './timeControls';
import { useTranslation } from 'react-i18next';

const AXIS_HORIZONTAL_MARGINS = 12;

const getTimeScale = (rangeEnd, datetimes, startTime, endTime) =>
  scaleTime()
    .domain([
      startTime ? moment(startTime).toDate() : first(datetimes),
      endTime ? moment(endTime).toDate() : last(datetimes),
    ])
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

const createChangeAndInputHandler =
  (datetimes, onChange, setAnchoredTimeIndex, setTooltipPos) => (ev) => {
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
  const nightTimes = useCurrentNightTimes();

  const timeScale = useMemo(
    () => getTimeScale(width, datetimes, startTime, endTime),
    [width, datetimes, startTime, endTime]
  );

  const startTimeValue = timeScale.domain()[0].valueOf();
  const endTimeValue = timeScale.domain()[1].valueOf();

  // Creating a scale for the night-time background gradients
  const gradientScale = useMemo(
    () => getTimeScale(100, nightTimes, startTimeValue, endTimeValue),
    [nightTimes, timeScale]
  );

  const nightTimeSets = nightTimes.flatMap(([start, end]) => [
    {
      start: Math.max(0, gradientScale(start)),
      end: Math.min(100, gradientScale(end)),
    },
  ]);

  const handleChangeAndInput = useMemo(
    () => createChangeAndInputHandler(datetimes, onChange, setAnchoredTimeIndex, setTooltipPos),
    [datetimes, onChange, setAnchoredTimeIndex]
  );

  if (!datetimes || datetimes.length === 0) return null;

  const selectedTimeValue = isNumber(selectedTimeIndex)
    ? datetimes[selectedTimeIndex].valueOf()
    : null;
  const anchoredTimeValue = isNumber(anchoredTimeIndex)
    ? datetimes[anchoredTimeIndex].valueOf()
    : null;

  const timeOnGradient = gradientScale(selectedTimeValue || anchoredTimeValue || endTimeValue);
  const isSelectedTimeDuringNight = nightTimeSets.some(
    ({ start, end }) => timeOnGradient >= start && timeOnGradient <= end
  );

  const timeValue = selectedTimeValue || anchoredTimeValue || endTimeValue;

  return (
    <div className={className}>
      <TimeSliderTooltip
        onClose={() => setTooltipPos(null)}
        position={tooltipPos}
        date={new Date(timeValue)}
      />
      <TimeControls
        date={new Date(timeValue)}
        selectedTimeAggregate={selectedTimeAggregate}
        handleTimeAggregationChange={handleTimeAggregationChange}
      />
      <TimeSliderInput
        onChange={handleChangeAndInput}
        value={timeValue}
        nightTimeSets={nightTimeSets}
        isValueAtNight={isSelectedTimeDuringNight}
        min={startTimeValue}
        max={endTimeValue}
        onTooltipClose={() => setTooltipPos(null)}
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
