import React from 'react';
import { connect } from 'react-redux';
import TimeSlider from '../components/timeslider';
import { BottomSheet } from 'react-spring-bottom-sheet'
import 'react-spring-bottom-sheet/dist/style.css'

import {
  useCurrentDatetimes,
} from '../hooks/redux';
import { dispatchApplication } from '../store';

const handleZoneTimeIndexChange = (timeIndex) => {
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};

const handleTimeAggregationChange = (aggregate) => {
  console.log(aggregate);
  dispatchApplication('selectedTimeAggregate', aggregate);
};

const mapStateToProps = (state) => ({
  selectedZoneTimeIndex: state.application.selectedZoneTimeIndex,
  selectedTimeAggregate: state.application.selectedTimeAggregate
});

const TimeController = ({ selectedZoneTimeIndex, selectedTimeAggregate }) => {
  const datetimes = useCurrentDatetimes();
  const startTime = datetimes[0];
  const endTime = datetimes[datetimes.length - 1];

  return (
    <BottomSheet open={true} blocking={false}>
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
      </BottomSheet>
  );
};

export default connect(mapStateToProps)(TimeController);
