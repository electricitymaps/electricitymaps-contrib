/* eslint-disable react/jsx-no-target-blank */
/* eslint-disable jsx-a11y/anchor-has-content */
// TODO: re-enable rules
import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';

import { dispatchApplication } from '../../store';
import { useConditionalZoneHistoryFetch } from '../../hooks/fetch';
import {
  useCurrentZoneHistoryDatetimes,
  useCurrentZoneHistoryStartTime,
  useCurrentZoneHistoryEndTime,
} from '../../hooks/redux';
import TimeSlider from '../../components/timeslider';

import CountryPanel from './countrypanel';
import { useLocation } from 'react-router-dom';
import { useTranslation } from '../../helpers/translation';

const handleZoneTimeIndexChange = (timeIndex) => {
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};

const mapStateToProps = (state) => ({
  selectedZoneTimeIndex: state.application.selectedZoneTimeIndex,
});

const SocialButtons = styled.div`
  @media (max-width: 767px) {
    display: ${(props) => (props.pathname !== '/map' ? 'none !important' : 'block')};
  }
`;

const ZoneDetailsPanel = ({ selectedZoneTimeIndex }) => {
  const { i18n } = useTranslation();
  const datetimes = useCurrentZoneHistoryDatetimes();
  const startTime = useCurrentZoneHistoryStartTime();
  const endTime = useCurrentZoneHistoryEndTime();
  const location = useLocation();

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
        <SocialButtons className="social-buttons" pathname={location.pathname}>
          <div>
            {/* Facebook share */}
            <div
              className="fb-share-button"
              data-href="https://app.electricitymap.org/"
              data-layout="button_count"
            />
            {/* Twitter share */}
            <a
              className="twitter-share-button"
              data-url="https://app.electricitymap.org"
              data-via="electricitymap"
              data-lang={i18n.language}
            />
            {/* Slack */}
            <span className="slack-button">
              <a href="https://slack.tmrow.com" target="_blank" className="slack-btn">
                <span className="slack-ico" />
                <span className="slack-text">Slack</span>
              </a>
            </span>
          </div>
        </SocialButtons>
      </div>
    </div>
  );
};

export default connect(mapStateToProps)(ZoneDetailsPanel);
