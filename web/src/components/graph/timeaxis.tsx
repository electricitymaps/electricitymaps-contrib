import React from 'react';
import { TIME } from '../../helpers/constants';
import { formatDateTick } from '../../helpers/formatting';
import { useTranslation } from '../../helpers/translation';
import PulseLoader from 'react-spinners/PulseLoader';
import styled from 'styled-components';

// Frequency at which values are displayed for a tick
const TIME_TO_TICK_FREQUENCY = {
  hourly: 6,
  daily: 6,
  monthly: 1,
  yearly: 1,
};

const TimeSliderAxis = styled.svg`
  width: 100%;
  height: 22px;
  margin: -6px 2px 0;
  overflow: visible;
`;

const TickGroup = styled.g`
  font-size: 0.7em;
  font-family: 'Open Sans', sans-serif;
  @media (max-width: 767px) {
    font-size: 0.6em;
  }
`;

const LoadingWrapper = styled.div`
  height: 22px; // ensures there's no jump between loading and non-loading
`;

const renderTickValue = (v, idx, displayLive, lang, selectedTimeAggregate) => {
  const shouldDisplayLive = idx === 24 && displayLive;
  if (shouldDisplayLive) {
    return (
      <g>
        <circle cx="-1em" cy="1.15em" r="2" fill="red" />
        <text fill="#DE3054" y="9" x="5" dy="0.71em" fontWeight="bold">
          LIVE
        </text>
      </g>
    );
  } else {
    return (
      <text fill="currentColor" y="9" x="5" dy="0.71em">
        {formatDateTick(v, lang, selectedTimeAggregate)}
      </text>
    );
  }
};

const renderTick = (scale, val, idx, displayLive, lang, selectedTimeAggregate, isLoading) => {
  const shouldShowValue = idx % TIME_TO_TICK_FREQUENCY[selectedTimeAggregate] === 0 && !isLoading;
  return (
    <TickGroup key={`timeaxis-tick-${idx}`} className="tick" opacity={1} transform={`translate(${scale(val)},0)`}>
      <line stroke="currentColor" y2="6" opacity={shouldShowValue ? 0.5 : 0.2} />
      {shouldShowValue && renderTickValue(val, idx, displayLive, lang, selectedTimeAggregate)}
    </TickGroup>
  );
};

const TimeAxis = React.memo(
  ({
    className,
    scale,
    transform,
    displayLive,
    selectedTimeAggregate = TIME.HOURLY,
    datetimes = [],
    isLoading,
    inputRef,
  }) => {
    const [x1, x2] = scale.range();
    const { i18n } = useTranslation();

    if (isLoading) {
      return (
        <LoadingWrapper>
          <PulseLoader color="#7A878D" size={5} />
        </LoadingWrapper>
      );
    }

    return (
      <TimeSliderAxis className="time-slider-axis-container" ref={inputRef}>
        <g
          className={className}
          transform={transform}
          fill="none"
          textAnchor="middle"
          style={{ pointerEvents: 'none' }}
        >
          <path className="domain" stroke="currentColor" d={`M${x1 + 0.5},6V0.5H${x2 + 0.5}V6`} />
          {datetimes.map((v, idx) =>
            renderTick(scale, v, idx, displayLive, i18n.language, selectedTimeAggregate, isLoading)
          )}
        </g>
      </TimeSliderAxis>
    );
  }
);

export default TimeAxis;
