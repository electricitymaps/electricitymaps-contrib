import React from 'react';
import { connect } from 'react-redux';
import TimeSlider from '../components/timeslider';

import {
  useCurrentDatetimes,
} from '../hooks/redux';
import { dispatchApplication } from '../store';

const handleZoneTimeIndexChange = (timeIndex) => {
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};

const mapStateToProps = (state) => ({
  selectedZoneTimeIndex: state.application.selectedZoneTimeIndex,
});

const TimeController = ({ selectedZoneTimeIndex }) => {
  const datetimes = useCurrentDatetimes();
  const startTime = datetimes[0];
  const endTime = datetimes[datetimes.length - 1];

  return (
    <TimeSlider
      className="zone-time-slider"
      onChange={handleZoneTimeIndexChange}
      selectedTimeIndex={selectedZoneTimeIndex}
      datetimes={datetimes}
      startTime={startTime}
      endTime={endTime}
    />
    // <div className="i want connect">I want connect</div>
  );
};

export default connect(mapStateToProps)(TimeController);
