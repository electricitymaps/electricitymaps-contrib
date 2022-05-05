import React from 'react';
import { connect } from 'react-redux';
import TimeSlider from '../components/timeslider_new';

import { useCurrentDatetimes } from '../hooks/redux';
import { dispatchApplication } from '../store';

const handleZoneTimeIndexChange = (timeIndex) => {
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};

const handleTimeAggregationChange = (aggregate) => {
  dispatchApplication('selectedTimeAggregate', aggregate);
};

const mapStateToProps = (state) => ({
  selectedZoneTimeIndex: state.application.selectedZoneTimeIndex,
  selectedTimeAggregate: state.application.selectedTimeAggregate,
});

const TimeController = ({ selectedZoneTimeIndex, selectedTimeAggregate, enabled }) => {
  const datetimes = useCurrentDatetimes();
  const startTime = datetimes[0];
  const endTime = datetimes[datetimes.length - 1];

  if (!enabled) {
    return null;
  }

  return (
    <TimeSlider
      className="zone-time-slider"
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
