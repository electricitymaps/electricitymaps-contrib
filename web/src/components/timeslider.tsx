import React, { useMemo, useState } from 'react';
import { scaleTime } from 'd3-scale';
import sortedIndex from 'lodash.sortedindex';

import TimeAxis from './graph/timeaxis';
import { useRefWidthHeightObserver } from '../hooks/viewport';
import TimeSliderTooltip from './tooltips/timeslidertooltip';
import TimeControls from './timeControls';
import { useTranslation } from '../helpers/translation';
import { TIME } from '../helpers/constants';
import { useSelector } from 'react-redux';
import { TimeSliderInput } from './TimeSliderInput';
import TimeSliderHeader from './timesliderheader';
import styled from 'styled-components';

const HiddenOnMobile = styled.div`
  @media screen and (max-width: 480px) {
    display: none;
  }
`;

const AXIS_HORIZONTAL_MARGINS = 12;

const getTimeScale = (rangeEnd: any, datetimes: any, startTime: any, endTime: any) =>
  scaleTime()
    .domain([startTime ? new Date(startTime) : datetimes.at(0), endTime ? new Date(endTime) : datetimes.at(-1)])
    .range([0, rangeEnd]);

const updateTooltipPosition = (ev: any, setTooltipPos: any) => {
  const thumbSize = 25;
  const range = ev.target;
  const ratio = (range.value - range.min) / (range.max - range.min);
  const posY = range.getBoundingClientRect().y;
  const posX = thumbSize / 2 + ratio * range.offsetWidth - ratio * thumbSize;
  setTooltipPos({ x: posX, y: posY });
};

const createChangeAndInputHandler =
  (datetimes: any, onChange: any, setAnchoredTimeIndex: any, setTooltipPos: any) => (ev: any) => {
    const value = parseInt(ev.target.value, 10);
    updateTooltipPosition(ev, setTooltipPos);

    let index = sortedIndex(
      datetimes.map((t: any) => t.valueOf()),
      value
    );
    // If the slider is past the last datetime, we set index to null in order to use the scale end time.
    if (index >= datetimes.length) {
      index = 0; //TODO this was null, check it still works
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
}: any) => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { __ } = useTranslation();
  const { ref, width } = useRefWidthHeightObserver(2 * AXIS_HORIZONTAL_MARGINS);
  const [tooltipPos, setTooltipPos] = useState(null);
  const [anchoredTimeIndex, setAnchoredTimeIndex] = useState(null);
  const isLoading = useSelector((state) => (state as any).data.isLoadingGrid);
  const timeScale = useMemo(
    () => getTimeScale(width, datetimes, startTime, endTime),
    [width, datetimes, startTime, endTime]
  );

  const startTimeValue = timeScale.domain()[0].valueOf();
  const endTimeValue = timeScale.domain()[1].valueOf() || 1; // Ensures timeslider thumb is at the end at all times

  const handleChangeAndInput = useMemo(
    () => createChangeAndInputHandler(datetimes, onChange, setAnchoredTimeIndex, setTooltipPos),
    [datetimes, onChange, setAnchoredTimeIndex]
  );

  const selectedTimeValue = typeof selectedTimeIndex === 'number' ? datetimes[selectedTimeIndex]?.valueOf() : null;
  const anchoredTimeValue = typeof anchoredTimeIndex === 'number' ? datetimes[anchoredTimeIndex]?.valueOf() : null;

  const timeValue = selectedTimeValue || anchoredTimeValue || endTimeValue;

  return (
    <div className={className}>
      <TimeSliderTooltip
        onClose={() => setTooltipPos(null)}
        position={tooltipPos}
        date={new Date(timeValue)}
        disabled // Disabled for now. Part of history feature
      />
      <HiddenOnMobile>
        <TimeSliderHeader />
      </HiddenOnMobile>
      <TimeControls
        selectedTimeAggregate={selectedTimeAggregate}
        handleTimeAggregationChange={handleTimeAggregationChange}
      />
      <TimeSliderInput
        className="time-slider-input"
        type="range"
        onChange={handleChangeAndInput}
        onInput={onChange}
        value={timeValue}
        min={startTimeValue}
        max={endTimeValue}
        aria-label="Change selected time"
      />
      <TimeAxis
        // @ts-expect-error TS(2322): Type '{ inputRef: (newNode: any) => () => void; da... Remove this comment to see the full error message
        inputRef={ref}
        datetimes={datetimes}
        scale={timeScale}
        transform={`translate(${AXIS_HORIZONTAL_MARGINS}, 0)`}
        className="time-slider-axis"
        displayLive={selectedTimeAggregate === TIME.HOURLY}
        selectedTimeAggregate={selectedTimeAggregate}
        isLoading={isLoading}
      />
    </div>
  );
};

export default TimeSlider;
