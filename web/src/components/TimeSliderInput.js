import React from 'react';
import styled from 'styled-components';
import { sortBy } from 'lodash';

const COLORS = {
  DAY: '#EFEFEF',
  NIGHT: 'rgba(0, 0, 0, 0.15)',
};

const createGradient = (sets) =>
  sortBy(sets, 'end')
    .map(
      ({ start, end }) =>
        `${COLORS.DAY} ${start}%, ${COLORS.NIGHT} ${start}%, ${COLORS.NIGHT} ${end}%, ${COLORS.DAY} ${end}%`
    )
    .join(',\n');

export const StyledInput = styled.input`
  --time-gradient: linear-gradient(90deg, ${(props) => createGradient(props.nightTimeSets)});
`;

export const TimeSliderInput = ({
  onChange,
  value,
  nightTimeSets,
  isValueAtNight,
  min,
  max,
  onTooltipClose,
}) => {
  const timeClass = isValueAtNight ? 'night' : 'day';
  return (
    <StyledInput
      type="range"
      className={`time-slider-input ${timeClass}`}
      nightTimeSets={nightTimeSets}
      onChange={onChange}
      onInput={onChange}
      value={value}
      min={min}
      max={max}
      onMouseLeave={onTooltipClose}
      onMouseOut={onTooltipClose}
    />
  );
};
