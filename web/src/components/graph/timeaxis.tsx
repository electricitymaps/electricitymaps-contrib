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

const renderTickValue = (v: any, idx: any, displayLive: any, lang: any, selectedTimeAggregate: any) => {
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

const renderTick = (
  scale: any,
  val: any,
  idx: any,
  displayLive: any,
  lang: any,
  selectedTimeAggregate: any,
  isLoading: any
) => {
  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
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
    // @ts-expect-error TS(2339): Property 'className' does not exist on type '{}'.
    className,
    // @ts-expect-error TS(2339): Property 'scale' does not exist on type '{}'.
    scale,
    // @ts-expect-error TS(2339): Property 'transform' does not exist on type '{}'.
    transform,
    // @ts-expect-error TS(2339): Property 'displayLive' does not exist on type '{}'... Remove this comment to see the full error message
    displayLive,
    // @ts-expect-error TS(2339): Property 'selectedTimeAggregate' does not exist on... Remove this comment to see the full error message
    selectedTimeAggregate = TIME.HOURLY,
    // @ts-expect-error TS(2339): Property 'datetimes' does not exist on type '{}'.
    datetimes = [],
    // @ts-expect-error TS(2339): Property 'isLoading' does not exist on type '{}'.
    isLoading,
    // @ts-expect-error TS(2339): Property 'inputRef' does not exist on type '{}'.
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
          {datetimes.map((v: any, idx: any) =>
            renderTick(scale, v, idx, displayLive, i18n.language, selectedTimeAggregate, isLoading)
          )}
        </g>
      </TimeSliderAxis>
    );
  }
);

export default TimeAxis;
