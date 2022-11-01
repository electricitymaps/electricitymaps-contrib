import React from 'react';
import styled from 'styled-components';
import { connect } from 'react-redux';
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

const mapStateToProps = (state) => ({
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

  @include respond-to('small') {
    min-height: 50px;
    box-shadow: 0px 0px 12px 0px rgba(0, 0, 0, 0.1);
    z-index: 999; /* required for the box-shadow to overlay everything */
  }
`;

const RightHeader = styled.div`
  @media (min-width: 768px) {
    display: none !important;
  }

  @include respond-to('small') {
    font-size: 0.6em;
  }
`;

const HeaderContent = styled.div`
  @include respond-to('small') {
    display: flex;
    justify-content: space-between;
    width: 100%;
    font-size: 1rem;
    height: 50px;
    padding-top: 13px;
    padding-bottom: 13px;
    padding-left: 15px;
    padding-right: 15px;
    line-height: 24px;
    box-sizing: border-box;
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
    display: ${(props) => (props.pathname === '/map' ? 'none !important' : 'flex')};
  }
`;

const LogoContainer = styled.div`
  @include respond-to('small') {
    display: flex;
  }
`;

const ElectricityMapLogo = styled.div`
  display: inline-block;
  height: 25px;
  width: 130px;
  background-image: url(../images/electricitymap-logo.svg);
  background-size: cover;
`;

const LeftPanel = ({ isLeftPanelCollapsed }) => {
  const location = useLocation();

  // TODO: Do this better when <Switch> is pulled up the hierarchy.
  const collapsedClass = isLeftPanelCollapsed ? 'collapsed' : '';

  return (
    <Container pathname={location.pathname} className={`panel left-panel ${collapsedClass}`}>
      <MobileHeader id="mobile-header" className="brightmode">
        <HeaderContent>
          <LogoContainer>
            <ElectricityMapLogo />
          </LogoContainer>
          <RightHeader>
            <LastUpdatedTime />
          </RightHeader>
        </HeaderContent>
      </MobileHeader>

      <LeftPanelCollapseButton
        id="left-panel-collapse-button"
        className={`${collapsedClass}`}
        onClick={() => dispatchApplication('isLeftPanelCollapsed', !isLeftPanelCollapsed)}
        role="button"
        tabIndex="0"
        aria-label="toggle left panel visibility"
      >
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
