import React from 'react';
import styled from 'styled-components';

const COLORS = {
  DAY: '#EFEFEF',
  NIGHT: 'rgba(0, 0, 0, 0.15)',
};

const createGradient = (sets) =>
  sets
    .sort((a, b) => a.end - b.end)
    .map(
      ({ start, end }) =>
        `${COLORS.DAY} ${start}%, ${COLORS.NIGHT} ${start}%, ${COLORS.NIGHT} ${end}%, ${COLORS.DAY} ${end}%`
    )
    .join(',\n');

export const StyledInput = styled.input`
  --time-gradient: linear-gradient(90deg, ${(props) => createGradient(props.nightTimeSets)});
`;

export const TimeSliderInput = ({ onChange, value, nightTimeSets, isValueAtNight, min, max }) => {
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
    />
  );
};
