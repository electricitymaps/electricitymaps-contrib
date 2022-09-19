import React from 'react';
import styled from 'styled-components';
import { useTranslation } from '../../../helpers/translation';
import { useSelector } from 'react-redux';
import { CountryHistoryTitle } from '../../../components/countryhistorytitle';
import Icon from '../../../components/icon';
import Countryhistoryemissionsgraph from '../../../components/countryhistoryemissionsgraph';
import Countryhistorycarbongraph from '../../../components/countryhistorycarbongraph';
import { TIME } from '../../../helpers/constants';
import Countrytable from '../../../components/countrytable';
import Countryhistorymixgraph from '../../../components/countryhistorymixgraph';
import Countryhistorypricesgraph from '../../../components/countryhistorypricesgraph';
import CountryDataInfo from '../../../components/countrydatainfo';
import ContributorList from '../../../components/contributorlist';
import SocialButtons from '../socialbuttons';

const BySource = styled.div`
  font-size: smaller;
  position: relative;
  top: 0.8rem;
  margin-bottom: 5px;
`;

const ProContainer = styled.small`
  @media (max-width: 767px) {
    display: none !important;
  }
`;

const StyledSources = styled.div`
  // Provides extra space to scroll further than the timeController
  margin-bottom: 170px;
  @media (max-width: 767px) {
    margin-bottom: 40px;
  }
`;

export const CountryDetails = ({ tableDisplayEmissions, electricityMixMode, data }) => {
  const selectedTimeAggregate = useSelector((state) => state.application.selectedTimeAggregate);
  const { __ } = useTranslation();

  // Disable mix graph on aggregated consumption data because we do not
  // show exchanges yet.
  const isMixGraphOverlayEnabled =
    selectedTimeAggregate && selectedTimeAggregate !== TIME.HOURLY && electricityMixMode == 'consumption';

  const isDataEstimated = data.estimationMethod ? true : false;

  return (
    <React.Fragment>
      <BySource>
        {__(selectedTimeAggregate !== TIME.HOURLY ? 'country-panel.averagebysource' : 'country-panel.bysource')}
      </BySource>

      <Countrytable />

      <hr />
      <div className="country-history">
        <CountryHistoryTitle
          translationKey={tableDisplayEmissions ? 'country-history.emissions' : 'country-history.carbonintensity'}
        />
        <br />
        <ProContainer>
          <Icon iconName="file_download" size={16} />
          <a
            href="https://electricitymaps.com/?utm_source=app.electricitymaps.com&utm_medium=referral&utm_campaign=country_panel"
            target="_blank"
            rel="noreferrer"
          >
            {__('country-history.Getdata')}
          </a>
        </ProContainer>
        {tableDisplayEmissions ? <Countryhistoryemissionsgraph /> : <Countryhistorycarbongraph />}
        <CountryHistoryTitle
          translationKey={
            tableDisplayEmissions
              ? `country-history.emissions${electricityMixMode === 'consumption' ? 'origin' : 'production'}`
              : `country-history.electricity${electricityMixMode === 'consumption' ? 'origin' : 'production'}`
          }
        />
        <br />
        <ProContainer>
          <Icon iconName="file_download" size={16} />
          <a
            href="https://electricitymaps.com/?utm_source=app.electricitymap.org&utm_medium=referral&utm_campaign=country_panel"
            target="_blank"
            rel="noreferrer"
          >
            {__('country-history.Getdata')}
          </a>
        </ProContainer>
        <div className="country-history">
          {isMixGraphOverlayEnabled && (
            <div className="no-data-overlay visible">
              <div className="no-data-overlay-background" />
              <div
                className="no-data-overlay-message graph"
                dangerouslySetInnerHTML={{
                  __html: 'Temporarily disabled. <br/> Switch to production view',
                }}
              />
            </div>
          )}

          <Countryhistorymixgraph isOverlayEnabled={isMixGraphOverlayEnabled} />
        </div>

        {selectedTimeAggregate === TIME.HOURLY && (
          <>
            <CountryHistoryTitle translationKey={'country-history.electricityprices'} />
            <Countryhistorypricesgraph />
          </>
        )}
      </div>
      <hr />
      <StyledSources>
        {isDataEstimated && <CountryDataInfo text={__('country-panel.dataIsEstimated')} />}
        {selectedTimeAggregate !== TIME.HOURLY && <CountryDataInfo text={__('country-panel.exchangesAreMissing')} />}
        {__('country-panel.source')}
        {': '}
        <a
          href="https://github.com/tmrowco/electricitymap-contrib/blob/master/DATA_SOURCES.md#real-time-electricity-data-sources"
          target="_blank"
          rel="noreferrer"
        >
          <span className="country-data-source">{data.source || '?'}</span>
        </a>
        <small>
          {' '}
          (
          <span
            dangerouslySetInnerHTML={{
              __html: __(
                'country-panel.addeditsource',
                'https://github.com/tmrowco/electricitymap-contrib/tree/master/parsers'
              ),
            }}
          />
          )
        </small>{' '}
        {__('country-panel.helpfrom')}
        <ContributorList />
        <SocialButtons hideOnDesktop />
      </StyledSources>
    </React.Fragment>
  );
};
