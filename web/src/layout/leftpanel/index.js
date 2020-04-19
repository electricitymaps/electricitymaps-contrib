/* eslint-disable react/jsx-no-target-blank */
/* eslint-disable jsx-a11y/anchor-is-valid */
/* eslint-disable jsx-a11y/anchor-has-content */
// TODO: re-enable rules

import React from 'react';
import { connect } from 'react-redux';
import {
  Switch,
  Route,
  Redirect,
  useLocation,
} from 'react-router-dom';

import { useSearchParams } from '../../helpers/router';
import { usePageViewsTracker } from '../../hooks/tracking';
import { useSmallLoaderVisible } from '../../hooks/redux';
import LastUpdatedTime from '../../components/lastupdatedtime';

import FAQPanel from './faqpanel';
import MobileInfoTab from './mobileinfotab';
import ZoneDetailsPanel from './zonedetailspanel';
import ZoneListPanel from './zonelistpanel';

const HandleLegacyRoutes = () => {
  const searchParams = useSearchParams();

  const page = (searchParams.get('page') || 'map')
    .replace('country', 'zone')
    .replace('highscore', 'ranking');
  searchParams.delete('page');

  const zoneId = searchParams.get('countryCode');
  searchParams.delete('countryCode');

  return (
    <Redirect
      to={{
        pathname: zoneId ? `/zone/${zoneId}` : `/${page}`,
        search: searchParams.toString(),
      }}
    />
  );
};

// TODO: Move all styles from styles.css to here

const mapStateToProps = state => ({
  isLeftPanelCollapsed: state.application.isLeftPanelCollapsed,
  isMobile: state.application.isMobile,
});

const LeftPanel = ({ isLeftPanelCollapsed, isMobile }) => {
  const isLoaderVisible = useSmallLoaderVisible();
  const location = useLocation();

  usePageViewsTracker();

  // Hide the panel completely if looking at the map on mobile.
  // TODO: Do this better when <Switch> is pulled up the hierarchy.
  const panelHidden = isMobile && location.pathname === '/map';

  return (
    <div
      className={`panel left-panel ${isLeftPanelCollapsed ? 'collapsed' : ''}`}
      style={panelHidden ? { display: 'none' } : {}}
    >

      <div id="mobile-header" className="large-screen-hidden brightmode">
        <div className="header-content">
          <div className="logo">
            <div className="image" id="electricitymap-logo" />
          </div>
          <div className="right-header large-screen-hidden">
            {isLoaderVisible && <span id="small-loading" className="loading" />}
            <LastUpdatedTime />
          </div>
        </div>
      </div>

      {/* Render different content based on the current route */}
      <Switch>
        <Route exact path="/" component={HandleLegacyRoutes} />
        <Route path="/map" component={ZoneListPanel} />
        <Route path="/ranking" component={ZoneListPanel} />
        <Route path="/zone/:zoneId" component={ZoneDetailsPanel} />
        <Route path="/info" component={MobileInfoTab} />
        <Route path="/faq" component={FAQPanel} />
        {/* TODO: Consider adding a 404 page  */}
      </Switch>
    </div>
  );
};

export default connect(mapStateToProps)(LeftPanel);
