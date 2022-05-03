import React from 'react';
import { connect } from 'react-redux';

import { dispatchApplication } from '../../store';
import { useConditionalZoneHistoryFetch } from '../../hooks/fetch';
import {
  useCurrentZoneHistoryDatetimes,
  useCurrentZoneHistoryStartTime,
  useCurrentZoneHistoryEndTime,
} from '../../hooks/redux';
import TimeSlider from '../../components/timeslider';

import CountryPanel from './countrypanel';
import SocialButtons from './socialbuttons';
import { useParams } from 'react-router-dom';

const handleZoneTimeIndexChange = (timeIndex) => {
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};

const mapStateToProps = (state) => ({
  selectedZoneTimeIndex: state.application.selectedZoneTimeIndex,
});

const ZoneDetailsPanel = ({ selectedZoneTimeIndex }) => {
  const datetimes = useCurrentZoneHistoryDatetimes();
  const startTime = useCurrentZoneHistoryStartTime();
  const endTime = useCurrentZoneHistoryEndTime();

  // Fetch history for the current zone if it hasn't been fetched yet.
  useConditionalZoneHistoryFetch();

  return (
    <>
      <div className="left-panel-zone-details">
        <CountryPanel />
      </div>
      {/* <TimeSlider
        className="zone-time-slider"
        onChange={handleZoneTimeIndexChange}
        selectedTimeIndex={selectedZoneTimeIndex}
        datetimes={datetimes}
        startTime={startTime}
        endTime={endTime}
      /> */}
    </>
  );
};

export default connect(mapStateToProps)(ZoneDetailsPanel);
