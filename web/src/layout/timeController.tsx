import React from 'react';
import { connect } from 'react-redux';
import TimeSlider from '../components/timeslider';

import { useCurrentDatetimes } from '../hooks/redux';
import { dispatchApplication } from '../store';
import { useTrackEvent } from '../hooks/tracking';
import styled from 'styled-components';

const handleZoneTimeIndexChange = (timeIndex) => {
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};

const mapStateToProps = (state) => ({
  selectedZoneTimeIndex: state.application.selectedZoneTimeIndex,
  selectedTimeAggregate: state.application.selectedTimeAggregate,
});

const StyledTimeSlider = styled(TimeSlider)`
  padding: 12px 24px;
  background: white;
  left: 10px;
  bottom: 10px;
  border-radius: 15px;
  text-align: center;
  overflow-y: visible;
  width: calc((14vw + 16rem) - 70px); // Ensures it is smaller than countrypanel
  z-index: 99;
  position: fixed;
  box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.3);

  .domain {
    display: none;
  }
  @media (max-width: 767px) {
    width: auto;
  }

  @media (max-width: 480px) {
    width: auto;
    box-shadow: none;
    padding: 0px 12px;
    height: auto;
    border-radius: 0;
    position: relative;
    bottom: auto;
    left: auto;
  }
`;

const TimeController = ({ selectedZoneTimeIndex, selectedTimeAggregate }) => {
  const datetimes = useCurrentDatetimes();
  const trackEvent = useTrackEvent();

  const startTime = datetimes.at(0);
  const endTime = datetimes.at(-1);

  const handleTimeAggregationChange = (aggregate, zoneDatetimes) => {
    if (aggregate === selectedTimeAggregate) {
      return;
    }
    trackEvent('AggregateButton Clicked', { aggregate });
    dispatchApplication('selectedTimeAggregate', aggregate);
    if (zoneDatetimes[aggregate]) {
      // set selectedZoneTimeIndex to max of datetimes (all the way to the right)
      // if we know already the size of the datetimes array
      dispatchApplication('selectedZoneTimeIndex', zoneDatetimes[aggregate].length - 1);
    }
  };

  return (
    <StyledTimeSlider
      onChange={handleZoneTimeIndexChange}
      selectedTimeIndex={selectedZoneTimeIndex}
      handleTimeAggregationChange={handleTimeAggregationChange}
      selectedTimeAggregate={selectedTimeAggregate}
      datetimes={datetimes}
      startTime={startTime}
      endTime={endTime}
    />
  );
};

export default connect(mapStateToProps)(TimeController);
