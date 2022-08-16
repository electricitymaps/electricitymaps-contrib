import React from 'react';
import styled from 'styled-components';
import { connect } from 'react-redux';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'reac... Remove this comment to see the full error message
import { Switch, Route, Redirect, useLocation } from 'react-router-dom';

import { dispatchApplication } from '../../store';
import { useSearchParams } from '../../hooks/router';
import LastUpdatedTime from '../../components/lastupdatedtime';
import Icon from '../../components/icon';

import FAQPanel from './faqpanel';
import MobileInfoTab from './mobileinfotab';
import ZoneDetailsPanel from './zonedetailspanel';
import ZoneListPanel from './zonelistpanel';

const HandleLegacyRoutes = () => {
  const searchParams = useSearchParams();

  const page = (searchParams.get('page') || 'map').replace('country', 'zone').replace('highscore', 'ranking');
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

const mapStateToProps = (state: any) => ({
  isLeftPanelCollapsed: state.application.isLeftPanelCollapsed,
});

const LeftPanelCollapseButton = styled.div`
  @media (max-width: 767px) {
    display: none !important;
  }
`;

const MobileHeader = styled.div`
  @media (min-width: 768px) {
    display: none !important;
  }

  padding-top: 0px;

  /* iOS Safari 11.2, Safari 11 */
  padding-top: constant(safe-area-inset-top, 0px);

  /* iOS Safari 11.4+, Safari 11.1+, Chrome 69+, Opera 56+ */
  padding-top: env(safe-area-inset-top, 0px);
`;

const RightHeader = styled.div`
  @media (min-width: 768px) {
    display: none !important;
  }
`;

const Container = styled.div`
  // custom scrollbars in chrome
  div::-webkit-scrollbar {
    position: relative;
    width: 6px;
  }
  div::-webkit-scrollbar-track-piece {
    background: $light-gray;
    border-radius: 3px;
  }
  div::-webkit-scrollbar-thumb {
    background: lightgray;
    border-radius: 3px;
  }
  // Hide the panel completely if looking at the map on small screens.
  @media (max-width: 767px) {
    display: ${(props) => ((props as any).pathname === '/map' ? 'none !important' : 'flex')};
  }
`;

const LeftPanel = ({ isLeftPanelCollapsed }: any) => {
  const location = useLocation();

  // TODO: Do this better when <Switch> is pulled up the hierarchy.
  const collapsedClass = isLeftPanelCollapsed ? 'collapsed' : '';

  return (
    // @ts-expect-error TS(2769): No overload matches this call.
    <Container pathname={location.pathname} className={`panel left-panel ${collapsedClass}`}>
      <MobileHeader id="mobile-header" className="brightmode">
        <div className="header-content">
          <div className="logo">
            <div className="image" id="electricitymap-logo" />
          </div>
          <RightHeader className="right-header">
            <LastUpdatedTime />
          </RightHeader>
        </div>
      </MobileHeader>

      <LeftPanelCollapseButton
        id="left-panel-collapse-button"
        className={`${collapsedClass}`}
        onClick={() => dispatchApplication('isLeftPanelCollapsed', !isLeftPanelCollapsed)}
        role="button"
        // @ts-expect-error TS(2769): No overload matches this call.
        tabIndex="0"
        aria-label="toggle left panel visibility"
      >
        {/* @ts-expect-error TS(2322): Type '{ iconName: string; }' is not assignable to ... Remove this comment to see the full error message */}
        <Icon iconName={!isLeftPanelCollapsed ? 'arrow_left' : 'arrow_right'} />
      </LeftPanelCollapseButton>

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
    </Container>
  );
};

export default connect(mapStateToProps)(LeftPanel);
