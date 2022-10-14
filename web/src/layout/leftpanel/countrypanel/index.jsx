import React, { useEffect, useMemo } from 'react';
import { Redirect, useLocation, useParams, useHistory } from 'react-router-dom';
import { connect, useSelector } from 'react-redux';
import styled from 'styled-components';
import LoadingPlaceholder from '../../../components/loadingplaceholder';
import { RetryBanner } from '../../../components/retrybanner';
import { dispatchApplication } from '../../../store';
import { useCurrentZoneData } from '../../../hooks/redux';
import { useTrackEvent } from '../../../hooks/tracking';
import { useTranslation } from '../../../helpers/translation';
import { TIME } from '../../../helpers/constants';
import { CountryOverview } from './countryOverview';
import { CountryDetails } from './countryDetails';
import { CountryHeader } from './countryHeader';
import { useAggregatesEnabled, useSearchParams } from '../../../hooks/router';

const mapStateToProps = (state) => ({
  electricityMixMode: state.application.electricityMixMode,
  isMobile: state.application.isMobile,
  tableDisplayEmissions: state.application.tableDisplayEmissions,
  zones: state.data.zones,
});

const LoadingWrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
`;

const CountryPanelWrap = styled.div`
  overflow-y: scroll;
  padding: 0 1.5rem;
  @media (max-width: 767px) {
    position: relative;
    padding-top: 0;
    overflow: hidden;
  }
`;

const LoadingText = styled.p`
  margin-top: 2px;
`;

const CountryPanelStyled = styled.div`
  display: flex;
  flex-direction: column;
  overflow-y: hidden;
  margin: 0;
  flex: 1 1 0px;
  @media (max-width: 767px) {
    margin: 0;
    display: block;
    overflow-y: scroll;
    -webkit-overflow-scrolling: touch;
    -moz-user-select: none; /* Selection disabled on firefox to avoid android "select all" button popping up when pressing graphs */
    margin-bottom: 60px; /* height of time-slider plus padding*/
  }
`;

const CountryPanel = ({ electricityMixMode, isMobile, tableDisplayEmissions, zones }) => {
  const { __ } = useTranslation();
  const isLoadingHistories = useSelector((state) => state.data.isLoadingHistories);
  const isLoadingGrid = useSelector((state) => state.data.isLoadingGrid);
  const failedRequestType = useSelector((state) => state.data.failedRequestType);
  const trackEvent = useTrackEvent();
  const history = useHistory();
  const location = useLocation();
  const { zoneId } = useParams();
  const isAggregateEnabled = useAggregatesEnabled();
  const searchParams = useSearchParams();

  const timeAggregate = useSelector((state) => state.application.selectedTimeAggregate);
  const data = useCurrentZoneData() || {};

  const parentPage = useMemo(() => {
    return {
      pathname: '/map',
      search: location.search,
    };
  }, [location]);

  // Back button keyboard navigation
  useEffect(() => {
    const keyHandler = (e) => {
      if (e.key === 'Backspace' || e.key === '/') {
        history.push(parentPage);
      }
    };
    document.addEventListener('keyup', keyHandler);
    return () => {
      document.removeEventListener('keyup', keyHandler);
    };
  }, [history, parentPage]);

  // Redirect to the parent page if the zone is invalid.
  if (!zones[zoneId]) {
    return <Redirect to={parentPage} />;
  }

  // Redirect to the parent page if the zone is subzone and country view is enabled
  if (
    zones[zoneId].geography.properties.isHighestGranularity === true &&
    zones[zoneId].geography.properties.isAggregatedView === false &&
    isAggregateEnabled === true
  ) {
    searchParams.set('aggregated', true);
    history.push({ pathname: zones[zoneId].geography.properties.countryKey, search: searchParams.toString() });
  }
  // Redirect to the map if the country is aggregated and the zone view is enabled
  if (
    zones[zoneId].geography.properties.isHighestGranularity === false &&
    zones[zoneId].geography.properties.isAggregatedView === true &&
    isAggregateEnabled === false
  ) {
    history.push(parentPage);
  }

  const { hasParser } = data;

  const switchToZoneEmissions = () => {
    dispatchApplication('tableDisplayEmissions', true);
    trackEvent('PanelEmissionButton Clicked');
  };

  const switchToZoneProduction = () => {
    dispatchApplication('tableDisplayEmissions', false);
    trackEvent('PanelProductionButton Clicked');
  };

  if (isLoadingHistories || isLoadingGrid) {
    // display loading
    return (
      <CountryPanelStyled>
        <div id="country-table-header">
          <CountryHeader parentPage={parentPage} zoneId={zoneId} data={data} isMobile={isMobile} />
        </div>
        <LoadingWrapper>
          <LoadingPlaceholder height="2rem" />
          <LoadingText>Loading...</LoadingText>
        </LoadingWrapper>
      </CountryPanelStyled>
    );
  }

  return (
    <CountryPanelStyled>
      {failedRequestType === 'zone' && <RetryBanner failedRequestType={failedRequestType} />}
      <div id="country-table-header">
        <CountryHeader
          isDataAggregated={timeAggregate && timeAggregate !== TIME.HOURLY}
          parentPage={parentPage}
          zoneId={zoneId}
          data={data}
          isMobile={isMobile}
        />
        {hasParser && (
          <CountryOverview
            switchToZoneEmissions={switchToZoneEmissions}
            switchToZoneProduction={switchToZoneProduction}
            data={data}
            isMobile={isMobile}
            tableDisplayEmissions={tableDisplayEmissions}
            electricityMixMode={electricityMixMode}
          />
        )}
      </div>

      <CountryPanelWrap>
        {hasParser ? (
          <CountryDetails
            data={data}
            tableDisplayEmissions={tableDisplayEmissions}
            electricityMixMode={electricityMixMode}
          />
        ) : (
          <div className="zone-details-no-parser-message" data-test-id="no-parser-message">
            <span
              dangerouslySetInnerHTML={{
                __html: __(
                  'country-panel.noParserInfo',
                  'https://github.com/tmrowco/electricitymap-contrib/wiki/Getting-started'
                ),
              }}
            />
          </div>
        )}
      </CountryPanelWrap>
    </CountryPanelStyled>
  );
};

export default connect(mapStateToProps)(CountryPanel);
