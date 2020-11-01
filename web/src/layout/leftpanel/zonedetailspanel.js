/* eslint-disable react/jsx-no-target-blank */
/* eslint-disable jsx-a11y/anchor-has-content */
// TODO: re-enable rules
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

const handleZoneTimeIndexChange = (timeIndex) => {
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};

const mapStateToProps = state => ({
  selectedZoneTimeIndex: state.application.selectedZoneTimeIndex,
});

const ZoneDetailsPanel = ({ selectedZoneTimeIndex }) => {
  const datetimes = useCurrentZoneHistoryDatetimes();
  const startTime = useCurrentZoneHistoryStartTime();
  const endTime = useCurrentZoneHistoryEndTime();

  // Fetch history for the current zone if it hasn't been fetched yet.
  useConditionalZoneHistoryFetch();

  return (
    <div className="left-panel-zone-details">
      <CountryPanel />
      <div className="detail-bottom-section">
        <TimeSlider
          className="zone-time-slider"
          onChange={handleZoneTimeIndexChange}
          selectedTimeIndex={selectedZoneTimeIndex}
          datetimes={datetimes}
          startTime={startTime}
          endTime={endTime}
        />
        <div className="social-buttons small-screen-hidden">
          <div>
            { /* Facebook share */}
            <div
              className="fb-share-button"
              data-href="https://www.electricitymap.org/"
              data-layout="button_count"
            />
            { /* Twitter share */}
            <a
              className="twitter-share-button"
              data-url="https://www.electricitymap.org"
              data-via="electricitymap"
              data-lang={locale}
            />
            { /* Slack */}
            <span className="slack-button">
              <a href="https://slack.tmrow.com" target="_blank" className="slack-btn">
                <span className="slack-ico" />
                <span className="slack-text">Slack</span>
              </a>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default connect(mapStateToProps)(ZoneDetailsPanel);
