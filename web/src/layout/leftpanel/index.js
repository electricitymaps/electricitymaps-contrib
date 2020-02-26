/* eslint-disable react/jsx-no-target-blank */
/* eslint-disable jsx-a11y/anchor-is-valid */
/* eslint-disable jsx-a11y/anchor-has-content */
// TODO: re-enable rules

import React from 'react';
import { connect } from 'react-redux';
import moment from 'moment';

import { dispatch, dispatchApplication } from '../../store';

// Layout
import CountryPanel from './countrypanel';
import FAQLayout from './faq';
import InfoText from './infotext';
import MobileInfoTab from './mobileinfotab';
import ZoneList from '../../components/zonelist';

// Modules
import { __ } from '../../helpers/translation';
import SearchBar from '../../components/searchbar';
import TimeSlider from '../../components/timeslider';

const { co2Sub } = require('../../helpers/formatting');

const documentSearchKeyUpHandler = (key, currentPage, searchRef) => {
  if (key === '/' && (currentPage === 'map' || currentPage === 'country')) {
    // Reset input and focus
    if (searchRef.current) {
      searchRef.current.value = '';
      searchRef.current.focus();
    }
  } else if (key && key.match(/^[A-z]$/) && currentPage === 'map') {
    // If input is not focused, focus it and append the pressed key
    if (searchRef.current && searchRef.current !== document.activeElement) {
      searchRef.current.value += key;
      searchRef.current.focus();
    }
  }
};

const handleZoneTimeIndexChange = (newSelectedZoneTimeIndex, timestamps) => {
  dispatch({
    type: 'UPDATE_SLIDER_SELECTED_ZONE_TIME',
    payload: {
      // When slider is on last value, we set the value to null in order to use the current state.
      selectedZoneTimeIndex: newSelectedZoneTimeIndex === (timestamps.length - 1) ? null : newSelectedZoneTimeIndex,
    },
  });
};

// TODO: Move all styles from styles.css to here

const getSelectedZoneHistory = state =>
  state.data.histories[state.application.selectedZoneName] || [];

const mapStateToProps = state => ({
  isLeftPanelCollapsed: state.application.isLeftPanelCollapsed,
  selectedZoneTimeIndex: state.application.selectedZoneTimeIndex,
  zoneHistoryTimestamps: getSelectedZoneHistory(state).map(d => moment(d.stateDatetime).toDate()),
});

export default connect(mapStateToProps)(props => (
  <div className={`panel left-panel ${props.isLeftPanelCollapsed ? 'collapsed' : ''}`}>

    <div id="mobile-header" className="large-screen-hidden brightmode">
      <div className="header-content">
        <div className="logo">
          <div className="image" id="electricitymap-logo" />
        </div>
        <div className="right-header large-screen-hidden">
          <span id="small-loading" className="loading" />
          <span className="current-datetime-from-now" />
        </div>
      </div>
    </div>

    <div className="left-panel-zone-list">

      <div className="zone-list-header">
        <div className="title">
          {' '}
          {__('left-panel.zone-list-header-title')}
        </div>
        <div
          className="subtitle"
          dangerouslySetInnerHTML={{
            __html: co2Sub(__('left-panel.zone-list-header-subtitle')),
          }}
        />
      </div>

      <SearchBar
        className="zone-search-bar"
        placeholder={__('left-panel.search')}
        documentKeyUpHandler={documentSearchKeyUpHandler}
        searchHandler={query => dispatchApplication('searchQuery', query)}
      />

      <ZoneList />

      <InfoText />
    </div>

    <MobileInfoTab />
    <div className="left-panel-zone-details">
      <CountryPanel />
      <div className="detail-bottom-section">
        <TimeSlider
          className="zone-time-slider"
          onChange={handleZoneTimeIndexChange}
          selectedTimeIndex={props.selectedZoneTimeIndex}
          timestamps={props.zoneHistoryTimestamps}
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
    <FAQLayout />
  </div>
));
