import React from 'react';
import { connect } from 'react-redux';

// Components
import CircularGauge from '../components/circulargauge';

// Modules
import { getCurrentZoneData } from '../helpers/redux';

const { co2Sub } = require('../helpers/formatting');
const { __ } = require('../helpers/translation');

// TODO(olc): rename this file as inner is used somewhere else.
// Probably best to move everything to main.js and make many components

/*
  For now, components are directly connected to redux.
  We need a main component to start linking components together
*/
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

export default props => (
  <div
    style={{
      position: 'fixed', /* This is done in order to ensure that dragging will not affect the body */
      width: '100vw',
      height: 'inherit',
      display: 'flex',
      flexDirection: 'column', /* children will be stacked vertically */
      alignItems: 'stretch', /* force children to take 100% width */
    }}
  >
    <div id="header">
      <div id="header-content" className="brightmode">
        <div className="logo">
          <div className="image" id="electricitymap-logo" />
          <span className="maintitle small-screen-hidden">
            <span className="live" style={{ fontWeight: 'bold' }}>Live</span>
                        · <a href="https://api.electricitymap.org?utm_source=electricitymap.org&utm_medium=referral">API</a>
                        · <a href="https://medium.com/electricitymap?utm_source=electricitymap.org&utm_medium=referral">Blog</a>
          </span>
        </div>
      </div>
    </div>
    <div id="inner">
      <div id="loading" className="loading overlay" />

      <div id="embedded-error" className="overlay" style={{ backgroundColor: 'grey', display: 'none' }}>
              Embedding of the ElectricityMap has been deactivated. You can still access it at <a href="http://www.electricitymap.org" target="_blank">https://www.electricitymap.org</a>.<br />
              Please contact us at <a href="mailto:hello@tmrow.com">hello@tmrow.com</a> for more information.
      </div>

      <div className="panel left-panel">
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
            <div className="title"> { __('left-panel.zone-list-header-title') }</div>
            <div
              className="subtitle"
              dangerouslySetInnerHTML={{
                __html: co2Sub(__('left-panel.zone-list-header-subtitle')),
              }}
            />
          </div>

          <div className="zone-search-bar">
            <input placeholder={__('left-panel.search')} />
          </div>

          <div className="zone-list" />

          <div className="info-text small-screen-hidden">
            <p>
              <label className="checkbox-container">
                { __('legends.colorblindmode') }
                <input type="checkbox" id="checkbox-colorblind" />
                <span className="checkmark" />
              </label>
            </p>
            <p>
              { __('panel-initial-text.thisproject') }
              {' '}
              <a href="https://github.com/tmrowco/electricitymap-contrib" target="_blank">
                { __('panel-initial-text.opensource') }
              </a>
              {' ('}
              { __('panel-initial-text.see') }
              {' '}
              <a href="https://github.com/tmrowco/electricitymap-contrib#data-sources" target="_blank">
                { __('panel-initial-text.datasources') }
              </a>
              {'). '}
              <span
                dangerouslySetInnerHTML={{
                  __html: __(
                    'panel-initial-text.contribute',
                    'https://github.com/tmrowco/electricitymap-contrib#adding-a-new-country'
                  ),
                }}
              />
              {'.'}
            </p>
            <p>
              { __('footer.foundbugs') } <a href="https://github.com/tmrowco/electricitymap-contrib/issues/new" target="_blank">{ __('footer.here') }</a>.<br />
            </p>
            <p>
              { __('footer.likethisvisu') } <a href="https://docs.google.com/forms/d/e/1FAIpQLSc-_sRr3mmhe0bifigGxfAzgh97-pJFcwpwWZGLFc6vvu8laA/viewform?c=0&w=1" target="_blank">{ __('footer.loveyourfeedback') }</a>!
            </p>
            <p>
              { __('footer.faq-text') } <a className="faq-link" role="link" tabIndex="0">{ __('footer.faq') }</a>
            </p>
            <div className="social-buttons">
              <div>
                { /* Facebook share */ }
                <div
                  className="fb-share-button"
                  data-href="https://www.electricitymap.org/"
                  data-layout="button_count"
                />
                { /* Twitter share */ }
                <a
                  className="twitter-share-button"
                  data-url="https://www.electricitymap.org"
                  data-via="electricitymap"
                  data-lang={locale}
                />
                { /* Slack */ }
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

        <div className="mobile-info-tab large-screen-hidden">
          <div className="mobile-watermark brightmode">
            <a href="http://www.tmrow.com/mission?utm_source=electricitymap.org&utm_medium=referral&utm_campaign=watermark" target="_blank">
              <img src="images/built-by-tomorrow.svg" />
            </a>
            <div className="socialicons">
              <div
                className="fb-like"
                data-href="https://www.facebook.com/tmrowco"
                data-layout="button"
                data-action="like"
                data-size="small"
                data-show-faces="false"
              />
              <a
                className="twitter-follow-button"
                href="https://twitter.com/electricitymap"
                data-show-screen-name="false"
                data-show-count="false"
                data-lang={locale}
              />
            </div>
          </div>
          <div className="info-text">
            <p>
              <input type="checkbox" id="checkbox-colorblind" />
              <label htmlFor="checkbox-colorblind">{ __('legends.colorblindmode') }</label>
            </p>
            <p>
              { __('panel-initial-text.thisproject') } <a href="https://github.com/tmrowco/electricitymap-contrib" target="_blank">{ __('panel-initial-text.opensource') }</a> ({ __('panel-initial-text.see') } <a href="https://github.com/tmrowco/electricitymap-contrib#data-sources" target="_blank">{ __('panel-initial-text.datasources') }</a>). { __('panel-initial-text.contribute', 'https://github.com/tmrowco/electricitymap-contrib#adding-a-new-country') }.
            </p>
            <p>
              { __('footer.foundbugs') } <a href="https://github.com/tmrowco/electricitymap-contrib/issues/new" target="_blank">{ __('footer.here') }</a>.<br />
            </p>
            <p>
              { __('footer.likethisvisu') } <a href="https://docs.google.com/forms/d/e/1FAIpQLSc-_sRr3mmhe0bifigGxfAzgh97-pJFcwpwWZGLFc6vvu8laA/viewform?c=0&w=1" target="_blank">{ __('footer.loveyourfeedback') }</a>!
            </p>
          </div>
          <div className="social-buttons large-screen-hidden">
            <div>
              { /* Facebook share */ }
              <div
                className="fb-share-button"
                data-href="https://www.electricitymap.org/"
                data-layout="button_count"
              />
              { /* Twitter share */ }
              <a
                className="twitter-share-button"
                data-url="https://www.electricitymap.org"
                data-via="electricitymap"
                data-lang={locale}
              />
              { /* Slack */ }
              <span className="slack-button">
                <a href="https://slack.tmrow.co" target="_blank" className="slack-btn">
                  <span className="slack-ico" />
                  <span className="slack-text">Slack</span>
                </a>
              </span>
            </div>
          </div>

          <div className="mobile-faq-header">
            { __('misc.faq') }
          </div>
          <div className="mobile-faq" />
        </div>
        <div className="left-panel-zone-details">
          <div className="country-panel">
            <div id="country-table-header">
              <div className="left-panel-zone-details-toolbar">
                <span className="left-panel-back-button">
                  <i className="material-icons" aria-hidden="true">arrow_back</i>
                </span>
                <div className="country-name-time">
                  <div className="country-name-time-table">
                    <div style={{ display: 'table-cell' }}>
                      <img id="country-flag" className="flag" />
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
                    <div><span className="country-emission-intensity" />g</div>
                  </div>
                  <div className="country-col-headline">{ co2Sub(__('country-panel.carbonintensity')) }</div>
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
                  <div className="country-col-headline">{ co2Sub(__('country-panel.lowcarbon')) }</div>
                  <div className="country-col-subtext" />
                </div>
                <div className="country-col country-renewable-wrap">
                  <div id="country-renewable-gauge" className="country-gauge-wrap">
                    <CountryRenewableGauge />
                  </div>
                  <div className="country-col-headline">{ __('country-panel.renewable') }</div>
                </div>
              </div>
              <div className="country-show-emissions-wrap">
                <div className="menu">
                  <a id="production" href="javascript:toggleSource(false)" />
                            |
                  <a id="emissions" href="javascript:toggleSource(true)">{ co2Sub(__('country-panel.emissions')) }</a>
                </div>
              </div>
            </div>
            <div className="country-panel-wrap">
              <div className="referral-link" />
              <div className="bysource">
                { __('country-panel.bysource') }
              </div>
              <div className="country-table-container" />
              <div className="zone-details-no-parser-message">
                { __('country-panel.noParserInfo', 'https://github.com/tmrowco/electricitymap-contrib#adding-a-new-country') }
              </div>

              <hr />
              <div className="country-history">
                <div className="loading overlay" />
                <span className="country-history-title">
                  { co2Sub(__('country-history.carbonintensity24h')) }
                </span>
                <br />
                <small className="small-screen-hidden">
                  <i className="material-icons" aria-hidden="true">file_download</i> <a href="https://data.electricitymap.org/?utm_source=electricitymap.org&utm_medium=referral&utm_campaign=country_panel" target="_blank">{ __('country-history.Getdata') }</a>
                  <span className="pro"><i className="material-icons" aria-hidden="true">lock</i> pro</span>
                </small>
                <svg id="country-history-carbon" />

                <div className="loading overlay" />
                <span className="country-history-title" id="country-history-electricity-carbonintensity" />
                <br />
                <small className="small-screen-hidden">
                  <i className="material-icons" aria-hidden="true">file_download</i> <a href="https://data.electricitymap.org/?utm_source=electricitymap.org&utm_medium=referral&utm_campaign=country_panel" target="_blank">{ __('country-history.Getdata') }</a>
                  <span className="pro"><i className="material-icons" aria-hidden="true">lock</i> pro</span>
                </small>
                <svg id="country-history-mix" />

                <div className="loading overlay" />
                <span className="country-history-title">
                  { __('country-history.electricityprices24h') }
                </span>
                <svg id="country-history-prices" />
              </div>
              <hr />
              <div>
                { __('country-panel.source') }
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
                { __('country-panel.helpfrom')}
                <div className="contributors" />
              </div>
              <div className="social-buttons large-screen-hidden">
                <div>
                  { /* Facebook share */ }
                  <div
                    className="fb-share-button"
                    data-href="https://www.electricitymap.org/"
                    data-layout="button_count"
                  />
                  { /* Twitter share */ }
                  <a
                    className="twitter-share-button"
                    data-url="https://www.electricitymap.org"
                    data-via="electricitymap"
                    data-lang={locale}
                  />
                  { /* Slack */ }
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
          <div className="detail-bottom-section">
            <div className="zone-time-slider" />
            <div className="social-buttons small-screen-hidden">
              <div>
                { /* Facebook share */ }
                <div
                  className="fb-share-button"
                  data-href="https://www.electricitymap.org/"
                  data-layout="button_count"
                />
                { /* Twitter share */ }
                <a
                  className="twitter-share-button"
                  data-url="https://www.electricitymap.org"
                  data-via="electricitymap"
                  data-lang={locale}
                />
                { /* Slack */ }
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
        <div className="faq-panel">
          <div className="faq-header">
            <span className="left-panel-back-button">
              <i className="material-icons" aria-hidden="true">arrow_back</i>
            </span>
            <span className="title">{ __('misc.faq') }</span>
          </div>
          <div className="faq" />
        </div>

      </div>

      <div id="map-container">
        <div id="zones" className="map-layer" />
        <canvas id="wind" className="map-layer" />
        <canvas id="solar" className="map-layer" />
        <div id="watermark" className="watermark small-screen-hidden brightmode">
          <a href="http://www.tmrow.com/mission?utm_source=electricitymap.org&utm_medium=referral&utm_campaign=watermark" target="_blank">
            <div id="built-by-tomorrow" />
          </a>
        </div>
        <div className="floating-legend-container">
          <div className="floating-legend-mobile-header">
            <span>{ __('misc.legend') }</span>
            <i className="material-icons toggle-legend-button up">call_made</i>
            <i className="material-icons toggle-legend-button down visible">call_received</i>
          </div>
          <div className="wind-potential-legend floating-legend">
            <div className="legend-header">{ __('legends.windpotential') } <small>(m/s)</small></div>
            <svg className="wind-potential-bar potential-bar colorbar" />
          </div>
          <div className="solar-potential-legend floating-legend">
            <div className="legend-header">{ __('legends.solarpotential') } <small>(W/m<span className="sup">2</span>)</small></div>
            <svg className="solar-potential-bar potential-bar colorbar" />
          </div>
          <div className="co2-legend floating-legend">
            <div className="legend-header">{ co2Sub(__('legends.carbonintensity'))} <small>(gCO<span className="sub">2</span>eq/kWh)</small></div>
            <svg className="co2-colorbar colorbar potential-bar" />
          </div>
        </div>
        <div className="prodcons-toggle-container">
          <div className="production-toggle">
            <div className="production-toggle-active-overlay" />
            <div className="production-toggle-item production">
              { __('tooltips.production') }
            </div>
            <div className="production-toggle-item consumption">
              { __('tooltips.consumption') }
            </div>
          </div>
          <div className="production-toggle-info">
                      i
          </div>
          <div id="production-toggle-tooltip" className="layer-button-tooltip hidden">
            <div className="tooltip-container">
              <div className="tooltip-text"> { __('tooltips.cpinfo') }</div>
              <div className="arrow" />
            </div>
          </div>

        </div>
        <div className="layer-buttons-container">
          <div>
            <button className="layer-button language-select-button" />
            <div id="language-select-button-tooltip" className="layer-button-tooltip hidden">
              <div className="tooltip-container">
                <div className="tooltip-text">{ __('tooltips.selectLanguage') }</div>
                <div className="arrow" />
              </div>
            </div>
            <div id="language-select-container" className="hidden" />
          </div>
          <div>
            <button className="layer-button wind-button" />
            <div id="wind-layer-button-tooltip" className="layer-button-tooltip hidden">
              <div className="tooltip-container">
                <div className="tooltip-text">{ __('tooltips.showWindLayer') }</div>
                <div className="arrow" />
              </div>
            </div>
          </div>
          <div>
            <button className="layer-button solar-button" />
            <div id="solar-layer-button-tooltip" className="layer-button-tooltip hidden">
              <div className="tooltip-container">
                <div className="tooltip-text">{ __('tooltips.showSolarLayer') }</div>
                <div className="arrow" />
              </div>
            </div>
          </div>
          <div>
            <button className="layer-button brightmode-button" />
            <div id="brightmode-layer-button-tooltip" className="layer-button-tooltip hidden">
              <div className="tooltip-container">
                <div className="tooltip-text">{ __('tooltips.toggleDarkMode') }</div>
                <div className="arrow" />
              </div>
            </div>
          </div>
        </div>


      </div>

      <div id="connection-warning" className="flash-message">
        <div className="inner">{ __('misc.oops') } <a href="" onClick="window.retryFetch(); return false;">{ __('misc.retrynow') }</a>.</div>
      </div>
      <div id="new-version" className="flash-message">
        <div className="inner">{ __('misc.newversion') }</div>
      </div>

      <div id="left-panel-collapse-button" className="small-screen-hidden" role="button" tabIndex="0">
        <i className="material-icons">arrow_drop_down</i>
      </div>

      { /* end #inner */ }
    </div>
    <div id="tab">
      <div id="tab-content">
        <a className="list-item map-button">

          <img className="tab-icon-custom" src="images/electricitymap-icon.svg" />
          <span className="tab-label">{ __('mobile-main-menu.map') }</span>

        </a>
        <a className="list-item highscore-button">

          <i className="material-icons" aria-hidden="true">view_list</i>
          <span className="tab-label">{ __('mobile-main-menu.areas') }</span>

        </a>
        <a className="list-item info-button">

          <i className="material-icons" aria-hidden="true">info</i>
          <span className="tab-label">{ __('mobile-main-menu.about') }</span>

        </a>
      </div>
    </div>
  </div>
);
