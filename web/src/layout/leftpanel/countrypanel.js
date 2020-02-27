/* eslint-disable jsx-a11y/click-events-have-key-events */
/* eslint-disable jsx-a11y/no-static-element-interactions */
/* eslint-disable jsx-a11y/mouse-events-have-key-events */
/* eslint-disable react/jsx-no-target-blank */
/* eslint-disable jsx-a11y/anchor-is-valid */
/* eslint-disable jsx-a11y/anchor-has-content */
// TODO: re-enable rules

import React from 'react';
import { connect } from 'react-redux';

// Components
import CircularGauge from '../../components/circulargauge';
import ContributorList from '../../components/contributorlist';
import CountryHistoryCarbonGraph from '../../components/countryhistorycarbongraph';
import CountryHistoryMixGraph from '../../components/countryhistorymixgraph';
import CountryHistoryPricesGraph from '../../components/countryhistorypricesgraph';
import Tooltip from '../../components/tooltip';

// Modules
import { updateApplication } from '../../actioncreators';
import { getCurrentZoneData } from '../../helpers/redux';
import { __ } from '../../helpers/translation';

const { co2Sub } = require('../../helpers/formatting');
const tooltipHelper = require('../../helpers/tooltip');

// TODO: Move all styles from styles.css to here
// TODO: Remove all unecessary id and class tags

const CountryLowCarbonGauge = connect((state) => {
  const d = getCurrentZoneData(state);
  if (!d) {
    return { percentage: null };
  }
  const fossilFuelRatio = state.application.electricityMixMode === 'consumption'
    ? d.fossilFuelRatio
    : d.fossilFuelRatioProduction;
  const countryLowCarbonPercentage = fossilFuelRatio != null
    ? 100 - (fossilFuelRatio * 100)
    : null;
  return {
    percentage: countryLowCarbonPercentage,
  };
})(CircularGauge);
const CountryRenewableGauge = connect((state) => {
  const d = getCurrentZoneData(state);
  if (!d) {
    return { percentage: null };
  }
  const renewableRatio = state.application.electricityMixMode === 'consumption'
    ? d.renewableRatio
    : d.renewableRatioProduction;
  const countryRenewablePercentage = renewableRatio != null
    ? renewableRatio * 100 : null;
  return {
    percentage: countryRenewablePercentage,
  };
})(CircularGauge);

// TODO: Move to a proper React component
const lowcarbInfoTooltip = new Tooltip('#lowcarb-info-tooltip');

const mapStateToProps = state => ({
  electricityMixMode: state.application.electricityMixMode,
  tableDisplayEmissions: state.application.tableDisplayEmissions,
});
const mapDispatchToProps = dispatch => ({
  dispatchApplication: (k, v) => dispatch(updateApplication(k, v)),
});

class Component extends React.PureComponent {
  toggleSource = () => {
    this.props.dispatchApplication('tableDisplayEmissions', !this.props.tableDisplayEmissions);
  }

  render() {
    const { electricityMixMode, tableDisplayEmissions } = this.props;

    return (
      <div className="country-panel">
        <div id="country-table-header">
          <div className="left-panel-zone-details-toolbar">
            <span className="left-panel-back-button">
              <i className="material-icons" aria-hidden="true">arrow_back</i>
            </span>
            <div className="country-name-time">
              <div className="country-name-time-table">
                <div style={{ display: 'table-cell' }}>
                  <img id="country-flag" className="flag" alt="" />
                </div>

                <div style={{ display: 'table-cell' }}>
                  <div className="country-name" />
                  <div className="country-time">?</div>
                </div>
              </div>
            </div>
          </div>
          <div className="country-table-header-inner">
            <div className="country-col country-emission-intensity-wrap">
              <div id="country-emission-rect" className="country-col-box emission-rect emission-rect-overview">
                <div>
                  <span className="country-emission-intensity" />
                  g
                </div>
              </div>
              <div
                className="country-col-headline"
                dangerouslySetInnerHTML={{ __html: co2Sub(__('country-panel.carbonintensity')) }}
              />
              <div className="country-col-subtext">(gCO<span className="sub">2</span>eq/kWh)</div>
            </div>
            <div className="country-col country-lowcarbon-wrap">
              <div id="country-lowcarbon-gauge" className="country-gauge-wrap">
                <CountryLowCarbonGauge
                  onMouseOver={() => tooltipHelper.showLowCarbonDescription(lowcarbInfoTooltip)}
                  onMouseMove={(clientX, clientY) => lowcarbInfoTooltip.update(clientX, clientY)}
                  onMouseOut={() => lowcarbInfoTooltip.hide()}
                />
              </div>
              <div
                className="country-col-headline"
                dangerouslySetInnerHTML={{ __html: co2Sub(__('country-panel.lowcarbon')) }}
              />
              <div className="country-col-subtext" />
            </div>
            <div className="country-col country-renewable-wrap">
              <div id="country-renewable-gauge" className="country-gauge-wrap">
                <CountryRenewableGauge />
              </div>
              <div
                className="country-col-headline"
                dangerouslySetInnerHTML={{ __html: co2Sub(__('country-panel.renewable')) }}
              />
            </div>
          </div>
          <div className="country-show-emissions-wrap">
            <div className="menu">
              <a
                id="production"
                onClick={this.toggleSource}
                className={!tableDisplayEmissions ? 'selected' : null}
                dangerouslySetInnerHTML={{ __html: __(`country-panel.electricity${electricityMixMode}`) }}
              />
              |
              <a
                id="emissions"
                onClick={this.toggleSource}
                className={tableDisplayEmissions ? 'selected' : null}
                dangerouslySetInnerHTML={{ __html: co2Sub(__('country-panel.emissions')) }}
              />
            </div>
          </div>
        </div>
        <div className="country-panel-wrap">
          <div className="bysource">
            {__('country-panel.bysource')}
          </div>
          <div className="country-table-container" />
          <div className="zone-details-no-parser-message">
            <span dangerouslySetInnerHTML={{ __html: __('country-panel.noParserInfo', 'https://github.com/tmrowco/electricitymap-contrib#adding-a-new-region') }} />
          </div>

          <hr />
          <div className="country-history">
            <div className="loading overlay" />
            <span
              className="country-history-title"
              dangerouslySetInnerHTML={{ __html: co2Sub(__('country-history.carbonintensity24h')) }}
            />
            <br />
            <small className="small-screen-hidden">
              <i className="material-icons" aria-hidden="true">file_download</i> <a href="https://data.electricitymap.org/?utm_source=electricitymap.org&utm_medium=referral&utm_campaign=country_panel" target="_blank">{__('country-history.Getdata')}</a>
              <span className="pro"><i className="material-icons" aria-hidden="true">lock</i> pro</span>
            </small>

            <CountryHistoryCarbonGraph />

            <div className="loading overlay" />
            <span
              className="country-history-title"
              id="country-history-electricity-carbonintensity"
            >
              { tableDisplayEmissions
                ? __(`country-history.emissions${electricityMixMode === 'consumption' ? 'origin' : 'production'}24h`)
                : __(`country-history.electricity${electricityMixMode === 'consumption' ? 'origin' : 'production'}24h`)
              }
            </span>
            <br />
            <small className="small-screen-hidden">
              <i className="material-icons" aria-hidden="true">file_download</i> <a href="https://data.electricitymap.org/?utm_source=electricitymap.org&utm_medium=referral&utm_campaign=country_panel" target="_blank">{__('country-history.Getdata')}</a>
              <span className="pro"><i className="material-icons" aria-hidden="true">lock</i> pro</span>
            </small>

            <CountryHistoryMixGraph />

            <div className="loading overlay" />
            <span className="country-history-title">
              {__('country-history.electricityprices24h')}
            </span>

            <CountryHistoryPricesGraph />
          </div>
          <hr />
          <div>
            {__('country-panel.source')}
            {': '}
            <a href="https://github.com/tmrowco/electricitymap-contrib#real-time-electricity-data-sources" target="_blank">
              <span className="country-data-source" />
            </a>
            <small>
              {' ('}
              <span
                dangerouslySetInnerHTML={{
                  __html: __(
                    'country-panel.addeditsource',
                    'https://github.com/tmrowco/electricitymap-contrib/tree/master/parsers'
                  ),
                }}
              />
              {')'}
            </small>
            {' '}
            {__('country-panel.helpfrom')}
            <ContributorList />
          </div>
          <div className="social-buttons large-screen-hidden">
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
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(Component);
