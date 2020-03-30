/* eslint-disable jsx-a11y/click-events-have-key-events */
/* eslint-disable jsx-a11y/no-static-element-interactions */
/* eslint-disable jsx-a11y/mouse-events-have-key-events */
/* eslint-disable react/jsx-no-target-blank */
/* eslint-disable jsx-a11y/anchor-is-valid */
/* eslint-disable jsx-a11y/anchor-has-content */
// TODO: re-enable rules

import React from 'react';
import moment from 'moment';
import { connect } from 'react-redux';

// Components
import CircularGauge from '../../components/circulargauge';
import ContributorList from '../../components/contributorlist';
import CountryHistoryCarbonGraph from '../../components/countryhistorycarbongraph';
import CountryHistoryEmissionsGraph from '../../components/countryhistoryemissionsgraph';
import CountryHistoryMixGraph from '../../components/countryhistorymixgraph';
import CountryHistoryPricesGraph from '../../components/countryhistorypricesgraph';
import CountryTable from '../../components/countrytable';

import { dispatch } from '../../store';

// Modules
import { updateApplication } from '../../actioncreators';
import { getCurrentZoneData } from '../../selectors';
import { getCo2Scale } from '../../helpers/scales';
import { flagUri } from '../../helpers/flags';
import { getFullZoneName, __ } from '../../helpers/translation';
import { co2Sub } from '../../helpers/formatting';
import { LOW_CARBON_INFO_TOOLTIP_KEY, TIMESCALE } from '../../helpers/constants';

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

const showLowCarbonInfoTooltip = (x, y) => {
  dispatch({
    type: 'SHOW_TOOLTIP',
    payload: {
      displayMode: LOW_CARBON_INFO_TOOLTIP_KEY,
      position: { x, y },
    },
  });
};

const hideLowCarbonInfoTooltip = () => {
  dispatch({ type: 'HIDE_TOOLTIP' });
};

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  countryCode: state.application.selectedZoneName || '',
  data: getCurrentZoneData(state) || {},
  electricityMixMode: state.application.electricityMixMode,
  tableDisplayEmissions: state.application.tableDisplayEmissions,
  timescale: state.application.timescale,
});
const mapDispatchToProps = disp => ({
  dispatchApplication: (k, v) => disp(updateApplication(k, v)),
});

class Component extends React.PureComponent {
  toggleSource = () => {
    this.props.dispatchApplication('tableDisplayEmissions', !this.props.tableDisplayEmissions);
  }

  render() {
    const {
      colorBlindModeEnabled,
      countryCode,
      data,
      electricityMixMode,
      tableDisplayEmissions,
      timescale,
    } = this.props;

    const { hasParser } = data;
    const datetime = data.stateDatetime || data.datetime;
    const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
    const co2Intensity = electricityMixMode === 'consumption'
      ? data.co2intensity
      : data.co2intensityProduction;

    const timescaleTranslationKey = timescale === TIMESCALE.MONTHLY
      ? 'monthly'
      : '24h';

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
                  <img id="country-flag" className="flag" alt="" src={countryCode && flagUri(countryCode, 24)} />
                </div>

                <div style={{ display: 'table-cell' }}>
                  <div className="country-name">
                    {getFullZoneName(countryCode)}
                  </div>
                  <div className="country-time">
                    {datetime ? moment(datetime).format('LL LT') : ''}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {hasParser && (
            <React.Fragment>
              <div className="country-table-header-inner">
                <div className="country-col country-emission-intensity-wrap">
                  <div
                    id="country-emission-rect"
                    className="country-col-box emission-rect emission-rect-overview"
                    style={{ backgroundColor: co2ColorScale(co2Intensity) }}
                  >
                    <div>
                      <span className="country-emission-intensity">
                        {Math.round(co2Intensity) || '?'}
                      </span>
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
                      onMouseMove={showLowCarbonInfoTooltip}
                      onMouseOut={hideLowCarbonInfoTooltip}
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
            </React.Fragment>
          )}
        </div>

        <div className="country-panel-wrap">
          {hasParser ? (
            <React.Fragment>
              <div className="bysource">
                {__('country-panel.bysource')}
              </div>

              <CountryTable />

              <hr />
              <div className="country-history">
                <div className="loading overlay" />
                <span className="country-history-title">
                  {co2Sub(__(
                    tableDisplayEmissions
                      ? `country-history.emissions${timescaleTranslationKey}`
                      : `country-history.carbonintensity${timescaleTranslationKey}`
                  ))}
                </span>
                <br />
                <small className="small-screen-hidden">
                  <i className="material-icons" aria-hidden="true">file_download</i> <a href="https://data.electricitymap.org/?utm_source=electricitymap.org&utm_medium=referral&utm_campaign=country_panel" target="_blank">{__('country-history.Getdata')}</a>
                  <span className="pro"><i className="material-icons" aria-hidden="true">lock</i> pro</span>
                </small>

                {tableDisplayEmissions ? <CountryHistoryEmissionsGraph /> : <CountryHistoryCarbonGraph />}

                <div className="loading overlay" />
                <span className="country-history-title">
                  {tableDisplayEmissions
                    ? __(`country-history.emissions${electricityMixMode === 'consumption' ? 'origin' : 'production'}${timescaleTranslationKey}`)
                    : __(`country-history.electricity${electricityMixMode === 'consumption' ? 'origin' : 'production'}${timescaleTranslationKey}`)
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
                  {__(`country-history.electricityprices${timescaleTranslationKey}`)}
                </span>

                <CountryHistoryPricesGraph />
              </div>
              <hr />
              <div>
                {__('country-panel.source')}
                {': '}
                <a href="https://github.com/tmrowco/electricitymap-contrib#real-time-electricity-data-sources" target="_blank">
                  <span className="country-data-source">{data.source || '?'}</span>
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
            </React.Fragment>
          ) : (
            <div className="zone-details-no-parser-message">
              <span dangerouslySetInnerHTML={{ __html: __('country-panel.noParserInfo', 'https://github.com/tmrowco/electricitymap-contrib#adding-a-new-region') }} />
            </div>
          )}

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
