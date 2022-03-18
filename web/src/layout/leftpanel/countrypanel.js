/* eslint-disable jsx-a11y/anchor-has-content */
/* eslint-disable jsx-a11y/mouse-events-have-key-events */
/* eslint-disable react/jsx-no-target-blank */
// TODO: re-enable rules

import React, { useEffect, useState } from 'react';
import {
  Redirect,
  Link,
  useLocation,
  useParams,
  useHistory,
} from 'react-router-dom';
import { connect, useSelector } from 'react-redux';
import { isNil, noop } from 'lodash';
import moment from 'moment';
import styled from 'styled-components';

// Components
import LowCarbonInfoTooltip from '../../components/tooltips/lowcarboninfotooltip';
import CarbonIntensitySquare from '../../components/carbonintensitysquare';
import CircularGauge from '../../components/circulargauge';
import ContributorList from '../../components/contributorlist';
import CountryHistoryCarbonGraph from '../../components/countryhistorycarbongraph';
import CountryHistoryEmissionsGraph from '../../components/countryhistoryemissionsgraph';
import CountryHistoryMixGraph from '../../components/countryhistorymixgraph';
import CountryHistoryPricesGraph from '../../components/countryhistorypricesgraph';
import CountryTable from '../../components/countrytable';
import CountryDisclaimer from '../../components/countrydisclaimer';
import LoadingPlaceholder from '../../components/loadingplaceholder';

import { dispatchApplication } from '../../store';

// Modules
import { useCurrentZoneData } from '../../hooks/redux';
import { useTrackEvent } from '../../hooks/tracking';
import { flagUri } from '../../helpers/flags';
import { getZoneNameWithCountry, __ } from '../../helpers/translation';
import EstimatedLabel from '../../components/countryestimationlabel';
import SocialButtons from './socialbuttons';

// TODO: Move all styles from styles.css to here
// TODO: Remove all unecessary id and class tags

const CountryLowCarbonGauge = (props) => {
  const electricityMixMode = useSelector(state => state.application.electricityMixMode);

  const d = useCurrentZoneData();
  if (!d) {
    return <CircularGauge {...props} />;
  }

  const fossilFuelRatio = electricityMixMode === 'consumption'
  ? d.fossilFuelRatio
  : d.fossilFuelRatioProduction;
  const countryLowCarbonPercentage = fossilFuelRatio !== null
  ? 100 - (fossilFuelRatio * 100)
  : null;

  return <CircularGauge percentage={countryLowCarbonPercentage} {...props} />;
};

const CountryRenewableGauge = (props) => {
  const electricityMixMode = useSelector(state => state.application.electricityMixMode);

  const d = useCurrentZoneData();
  if (!d) {
    return <CircularGauge {...props} />;
  }

  const renewableRatio = electricityMixMode === 'consumption'
  ? d.renewableRatio
  : d.renewableRatioProduction;
  const countryRenewablePercentage = renewableRatio !== null
  ? renewableRatio * 100
  : null;

  return <CircularGauge percentage={countryRenewablePercentage} {...props} />;
};

const mapStateToProps = state => ({
  electricityMixMode: state.application.electricityMixMode,
  isMobile: state.application.isMobile,
  tableDisplayEmissions: state.application.tableDisplayEmissions,
  zones: state.data.grid.zones,
});

const Flag = styled.img`
  vertical-align: bottom;
  padding-right: .8rem;
`;

const CountryTime = styled.div`
  white-space: nowrap;
`;

const IconContainer = styled.small`
  @media (max-width: 767px) {
    display: none !important;
  }
`;

const CountryNameTime = styled.div`
  font-size: smaller;
  margin-left: 25px;
`;

const CountryNameTimeTable = styled.div`
  display: flex;
  justify-content: space-between;
  margin-left: 1.2rem;
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

const BySource = styled.div`
  font-size: smaller;
  position: relative;
  top: 0.8rem;
`;

const CountryHistoryTitle = styled.span`
  font-size: 1.1em;
`;

const CountryTableHeaderInner = styled.div`
  display: flex;
  flex-basis: 33.3%;
  justify-content: space-between;
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
    margin-bottom: 60px; /* height of .zone-time-slider plus padding*/
  }
`;

const EstimatedDataInfoBox = styled.p`
  background-color: #eee;
  border-radius: 6px;
  padding: 6px;
  font-size: .75rem;
  margin: 1rem 0;
`;

const EstimatedDataInfo = () => (
  <React.Fragment>
    <EstimatedDataInfoBox
      dangerouslySetInnerHTML={{
        __html: __('country-panel.dataIsEstimated'),
      }}
    />
    <hr />
  </React.Fragment>
);

const CountryPanel = ({
  electricityMixMode,
  isMobile,
  tableDisplayEmissions,
  zones,
}) => {
  const [tooltip, setTooltip] = useState(null);

  const isLoadingHistories = useSelector(state => state.data.isLoadingHistories);

  const trackEvent = useTrackEvent();
  const history = useHistory();
  const location = useLocation();
  const { zoneId } = useParams();

  const data = useCurrentZoneData() || {};

  const parentPage = {
    pathname: '/map',
    search: location.search,
  };

  // Back button keyboard navigation
  useEffect(
    () => {
      const keyHandler = (e) => {
        if (e.key === 'Backspace' || e.key === '/') {
          history.push(parentPage);
        }
      };
      document.addEventListener('keyup', keyHandler);
      return () => {
        document.removeEventListener('keyup', keyHandler);
      };
    },
    [history],
  );

  // Redirect to the parent page if the zone is invalid.
  if (!zones[zoneId]) {
    return <Redirect to={parentPage} />;
  }

  const { hasData, disclaimer, estimationMethod } = data;
  const isDataEstimated = !isNil(estimationMethod);

  const datetime = data.stateDatetime || data.datetime;
  const co2Intensity = electricityMixMode === 'consumption'
    ? data.co2intensity
    : data.co2intensityProduction;


  const switchToZoneEmissions = () => {
    dispatchApplication('tableDisplayEmissions', true);
    trackEvent('switchToCountryEmissions');
  };

  const switchToZoneProduction = () => {
    dispatchApplication('tableDisplayEmissions', false);
    trackEvent('switchToCountryProduction');
  };


  return (
    <CountryPanelStyled>
      <div id="country-table-header">
        <div className="left-panel-zone-details-toolbar">
          <Link to={parentPage}>
            <span className="left-panel-back-button">
              <i className="material-icons" aria-hidden="true">arrow_back</i>
            </span>
          </Link>
          <CountryNameTime>
            <CountryNameTimeTable>
              <div>
                <Flag id="country-flag" alt="" src={flagUri(zoneId, 24)} />
              </div>
              <div style={{ flexGrow: 1 }}>
                <div className="country-name">{getZoneNameWithCountry(zoneId)}</div>
                <CountryTime>
                  {datetime ? moment(datetime).format('LL LT') : ''}
                  {isDataEstimated && <EstimatedLabel isMobile={isMobile} />}
                </CountryTime>
              </div>
              {disclaimer && <CountryDisclaimer text={disclaimer} isMobile={isMobile} />}
            </CountryNameTimeTable>
          </CountryNameTime>
        </div>

        {hasData && (
          <React.Fragment>
            <CountryTableHeaderInner>
              <CarbonIntensitySquare value={co2Intensity} withSubtext />
              <div className="country-col country-lowcarbon-wrap">
                <div id="country-lowcarbon-gauge" className="country-gauge-wrap">
                  <CountryLowCarbonGauge
                    onClick={isMobile ? ((x, y) => setTooltip({ position: { x, y } })) : noop}
                    onMouseMove={!isMobile ? ((x, y) => setTooltip({ position: { x, y } })) : noop}
                    onMouseOut={() => setTooltip(null)}
                  />
                  {tooltip && (
                    <LowCarbonInfoTooltip
                      position={tooltip.position}
                      onClose={() => setTooltip(null)}
                    />
                  )}
                </div>
                <div className="country-col-headline">{__('country-panel.lowcarbon')}</div>
                <div className="country-col-subtext" />
              </div>
              <div className="country-col country-renewable-wrap">
                <div id="country-renewable-gauge" className="country-gauge-wrap">
                  <CountryRenewableGauge />
                </div>
                <div className="country-col-headline">{__('country-panel.renewable')}</div>
              </div>
            </CountryTableHeaderInner>
            <div className="country-show-emissions-wrap">
              <div className="menu">
                <a onClick={switchToZoneProduction} className={!tableDisplayEmissions ? 'selected' : null}>
                  {__(`country-panel.electricity${electricityMixMode}`)}
                </a>
                |
                <a onClick={switchToZoneEmissions} className={tableDisplayEmissions ? 'selected' : null}>
                  {__('country-panel.emissions')}
                </a>
              </div>
            </div>
          </React.Fragment>
        )}
      </div>

      <CountryPanelWrap>
        {hasData ? (
          <React.Fragment>
            <BySource>
              {__('country-panel.bysource')}
            </BySource>

            <CountryTable />

            <hr />
            {isDataEstimated && <EstimatedDataInfo />}
            <div className="country-history">
              <CountryHistoryTitle>
                {__(tableDisplayEmissions ? 'country-history.emissions24h' : 'country-history.carbonintensity24h')}
              </CountryHistoryTitle>
              <br />
              <IconContainer>
                <i className="material-icons" aria-hidden="true">file_download</i> <a href="https://electricitymap.org/?utm_source=app.electricitymap.org&utm_medium=referral&utm_campaign=country_panel" target="_blank">{__('country-history.Getdata')}</a>
                <span className="pro"><i className="material-icons" aria-hidden="true">lock</i> pro</span>
              </IconContainer>
              {/* TODO: Make the loader part of AreaGraph component with inferred height */}
              {isLoadingHistories ? <LoadingPlaceholder height="9.2em" /> : (
                tableDisplayEmissions ? <CountryHistoryEmissionsGraph /> : <CountryHistoryCarbonGraph />
              )}

              <CountryHistoryTitle>
                {tableDisplayEmissions
                  ? __(`country-history.emissions${electricityMixMode === 'consumption' ? 'origin' : 'production'}24h`)
                  : __(`country-history.electricity${electricityMixMode === 'consumption' ? 'origin' : 'production'}24h`)
                }
              </CountryHistoryTitle>
              <br />
              <IconContainer>
                <i className="material-icons" aria-hidden="true">file_download</i> <a href="https://electricitymap.org/?utm_source=app.electricitymap.org&utm_medium=referral&utm_campaign=country_panel" target="_blank">{__('country-history.Getdata')}</a>
                <span className="pro"><i className="material-icons" aria-hidden="true">lock</i> pro</span>
              </IconContainer>
              {/* TODO: Make the loader part of AreaGraph component with inferred height */}
              {isLoadingHistories ? <LoadingPlaceholder height="11.2em" /> : <CountryHistoryMixGraph />}

              <CountryHistoryTitle>
                {__('country-history.electricityprices24h')}
              </CountryHistoryTitle>
              {/* TODO: Make the loader part of AreaGraph component with inferred height */}
              {isLoadingHistories ? <LoadingPlaceholder height="7.2em" /> : <CountryHistoryPricesGraph />}
            </div>
            <hr />
            <div>
              {__('country-panel.source')}
              {': '}
              <a href="https://github.com/tmrowco/electricitymap-contrib/blob/master/DATA_SOURCES.md#real-time-electricity-data-sources" target="_blank">
                <span className="country-data-source">{data.source || '?'}</span>
              </a>
              <small>
                {' '}
                (
                <span
                  dangerouslySetInnerHTML={{
                    __html: __(
                      'country-panel.addeditsource',
                      'https://github.com/tmrowco/electricitymap-contrib/tree/master/parsers',
                    ),
                  }}
                />
                )
              </small>
              {' '}
              {__('country-panel.helpfrom')}
              <ContributorList />
            </div>
          </React.Fragment>
        ) : (
          <div className="zone-details-no-parser-message">
            <span dangerouslySetInnerHTML={{ __html: __('country-panel.noParserInfo', 'https://github.com/tmrowco/electricitymap-contrib/wiki/Getting-started') }} />
          </div>
        )}

        <SocialButtons hideOnDesktop />
      </CountryPanelWrap>
    </CountryPanelStyled>
  );
};

export default connect(mapStateToProps)(CountryPanel);
