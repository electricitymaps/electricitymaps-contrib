import styled, { css } from 'styled-components';

const thumb = css`
  -webkit-appearance: none;
  height: 26px;
  width: 26px;
  border-radius: 17px;
  cursor: pointer;
  margin-top: -8px;
  transition: box-shadow 0.4s;
  box-shadow: 0 0 5px 0 rgba(0, 0, 0, 0.15);
  border: 1px solid lightgray;
  background: #ffffff url('../images/slider-thumb.svg') center center no-repeat;
  background-size: 12px;
  border: none;
  box-shadow: 0.1px 0.1px 6px rgba(0, 0, 0, 0.16);

  &:hover {
    box-shadow: 0 0 15px 0 rgba(0, 0, 0, 0.15);
  }
`;

const track = css`
  width: 100%;
  height: 12px;
  border-radius: 4px;
  cursor: pointer;
  background: #f0f0f0;
  background-size: 100% 100%;
  background-repeat: no-repeat;
`;

export const TimeSliderInput = styled.input`
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

  // Webkit (Chrome, Edge, etc.)
  &::-webkit-slider-thumb {
    ${thumb}
  }
  ::-webkit-slider-runnable-track {
    ${track}
  }

  // Firefox
  &::-moz-range-thumb {
    ${thumb}
  }
  &::-moz-range-track {
    ${track}
  }
`;
