import React from 'react';
import { connect } from 'react-redux';

import { dispatch } from '../../store';
import {
  getSelectedZoneHistoryDatetimes,
  getZoneHistoryStartTime,
  getZoneHistoryEndTime,
} from '../../selectors';
import TimeSlider from '../../components/timeslider';

import CountryPanel from './countrypanel';

const handleZoneTimeIndexChange = (selectedZoneTimeIndex) => {
  dispatch({
    type: 'UPDATE_SLIDER_SELECTED_ZONE_TIME',
    payload: { selectedZoneTimeIndex },
  });
};

const mapStateToProps = state => ({
  selectedZoneTimeIndex: state.application.selectedZoneTimeIndex,
  zoneHistoryDatetimes: getSelectedZoneHistoryDatetimes(state),
  zoneHistoryStartTime: getZoneHistoryStartTime(state),
  zoneHistoryEndTime: getZoneHistoryEndTime(state),
});

const ZoneDetailsPanel = ({
  selectedZoneTimeIndex,
  zoneHistoryDatetimes,
  zoneHistoryStartTime,
  zoneHistoryEndTime,
}) => (
  <div className="left-panel-zone-details">
    <CountryPanel />
    <div className="detail-bottom-section">
      <TimeSlider
        className="zone-time-slider"
        onChange={handleZoneTimeIndexChange}
        selectedTimeIndex={selectedZoneTimeIndex}
        datetimes={zoneHistoryDatetimes}
        startTime={zoneHistoryStartTime}
        endTime={zoneHistoryEndTime}
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
            <a href="https://slack.tmrow.co" target="_blank" className="slack-btn">
              <span className="slack-ico" />
              <span className="slack-text">Slack</span>
            </a>
          </span>
        </div>
      </div>
    </div>
  </div>
);

export default connect(mapStateToProps)(ZoneDetailsPanel);
