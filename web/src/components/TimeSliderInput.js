import React from 'react';
import styled from 'styled-components';
import { sortBy } from 'lodash';

const COLORS = {
  DAY: '#EFEFEF',
  NIGHT: '#666', // TODO: Find proper color
};

const getStyling = sets => sortBy(sets, 'end')
  .map(
    ({ start, end }) => `${COLORS.DAY} ${start}%, ${COLORS.NIGHT} ${start}%, ${COLORS.NIGHT} ${end}%, ${COLORS.DAY} ${end}%`,
  )
  .join(',\n');

export const StyledInput = styled.input`
  --time-gradient: linear-gradient(
    90deg,
    ${props => getStyling(props.nightSets)}
  );
`;

// TODO: Test performance
export const TimeSliderInput = ({
  onChange, value, nightTimeSets, isValueAtNight, min, max,
}) => {
  const timeClass = isValueAtNight ? 'night' : 'day';
  return (
    <StyledInput
      type="range"
      className={`time-slider-input ${timeClass}`}
      nightSets={nightTimeSets}
      onChange={onChange}
      onInput={onChange}
      value={value}
      min={min}
      max={max}
    />
  );
};
