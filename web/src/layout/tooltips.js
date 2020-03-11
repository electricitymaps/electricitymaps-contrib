import React from 'react';
import { connect } from 'react-redux';

// Components
import CountryPanelExchangeTooltip from '../components/tooltips/countrypanelexchangetooltip';
import LowCarbonInfoTooltip from '../components/tooltips/lowcarboninfotooltip';
import MapExchangeTooltip from '../components/tooltips/mapexchangetooltip';
import PriceTooltip from '../components/tooltips/pricetooltip';
import CircularGauge from '../components/circulargauge';

const { co2Sub } = require('../helpers/formatting');
const { __ } = require('../helpers/translation');

const TooltipLowCarbonGauge = connect(state => ({
  percentage: state.application.tooltipLowCarbonGaugePercentage,
}))(CircularGauge);
const TooltipRenewableGauge = connect(state => ({
  percentage: state.application.tooltipRenewableGaugePercentage,
}))(CircularGauge);

export default () => (
  <React.Fragment>
    <div id="country-tooltip" className="tooltip panel">
      <div className="zone-name-header">
        <img id="country-flag" className="flag" />
        {' '}
        <span id="country-name" />
      </div>
      <div className="zone-details">
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
          </div>
          <div className="country-col country-lowcarbon-wrap">
            <div id="tooltip-country-lowcarbon-gauge" className="country-gauge-wrap">
              <TooltipLowCarbonGauge />
            </div>
            <div
              className="country-col-headline"
              dangerouslySetInnerHTML={{ __html: co2Sub(__('country-panel.lowcarbon')) }}
            />
            <div className="country-col-subtext" />
          </div>
          <div className="country-col country-renewable-wrap">
            <div id="tooltip-country-renewable-gauge" className="country-gauge-wrap">
              <TooltipRenewableGauge />
            </div>
            <div className="country-col-headline">{__('country-panel.renewable')}</div>
          </div>
        </div>
      </div>
      <div className="temporary-outage-text">
        {__('tooltips.temporaryDataOutage')}
      </div>
      <div className="no-parser-text">
        <span dangerouslySetInnerHTML={{ __html: __('tooltips.noParserInfo', 'https://github.com/tmrowco/electricitymap-contrib#adding-a-new-region') }} />
      </div>
    </div>
    <MapExchangeTooltip />
    <PriceTooltip />
    <div id="countrypanel-production-tooltip" className="tooltip panel">
      <span id="line1" />
      <br />
      <small>
        (
        <span id="production-proportion-detail" />
        )
      </small>
      <br />
      <span className="production-visible">
        <br />
        {__('tooltips.utilizing')}
        {' '}
        <b><span id="capacity-factor" /></b>
        {' '}
        {__('tooltips.ofinstalled')}
        <br />
        <small>
          (
          <span id="capacity-factor-detail" />
          )
        </small>
        <br />
        <br />
        <span dangerouslySetInnerHTML={{ __html: co2Sub(__('tooltips.withcarbonintensity')) }} />
        <br />
        <div className="emission-rect" />
        {' '}
        <span className="emission-intensity" />
        gCO
        <span className="sub">2</span>
        {'eq/kWh '}
        <small>
          (
          {__('country-panel.source')}
          {': '}
          <span className="emission-source" />
          )
        </small>
      </span>
    </div>
    <CountryPanelExchangeTooltip />
    <LowCarbonInfoTooltip />
  </React.Fragment>
);
