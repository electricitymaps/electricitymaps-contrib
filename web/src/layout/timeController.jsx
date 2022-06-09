import React from 'react';
import { connect } from 'react-redux';
import TimeSlider from '../components/timeslider_new';

import { useCurrentDatetimes } from '../hooks/redux';
import { useFeatureToggle } from '../hooks/router';
import { dispatchApplication } from '../store';
import styled from 'styled-components';

const handleZoneTimeIndexChange = (timeIndex) => {
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};

const handleTimeAggregationChange = (aggregate) => {
  dispatchApplication('selectedTimeAggregate', aggregate);
  // TODO: set index to the max of the range of selected time aggregate
  dispatchApplication('selectedZoneTimeIndex', null);
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

  .time-slider-axis-container {
    width: 100%;
    height: 20px;
    overflow: visible;
  }

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
  const isHistoryFeatureEnabled = useFeatureToggle('history');

  if (!isHistoryFeatureEnabled) {
    return null;
  }

  const startTime = datetimes.at(0);
  const endTime = datetimes.at(-1);

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
