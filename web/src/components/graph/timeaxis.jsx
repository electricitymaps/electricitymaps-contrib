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

const LoadingWrapper = styled.div`
  height: 25px; // ensures there's no jump between loading and non-loading
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
    <g key={`timeaxis-tick-${idx}`} className="tick" opacity={1} transform={`translate(${scale(val)},0)`}>
      <line stroke="currentColor" y2="6" opacity={shouldShowValue ? 0.5 : 0.2} />
      {shouldShowValue && renderTickValue(val, idx, displayLive, lang, selectedTimeAggregate)}
    </g>
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

    if (!isLoading) {
      return (
        <LoadingWrapper>
          <PulseLoader color="#7A878D" size={5} />
        </LoadingWrapper>
      );
    }

    return (
      <svg className="time-slider-axis-container" ref={inputRef}>
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
      </svg>
    );
  }
);

export default TimeAxis;
