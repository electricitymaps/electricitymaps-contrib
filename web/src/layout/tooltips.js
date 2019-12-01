import React from 'react';
import { connect } from 'react-redux';

// Components
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
            <div className="country-col-headline">{co2Sub(__('country-panel.carbonintensity'))}</div>
          </div>
          <div className="country-col country-lowcarbon-wrap">
            <div id="tooltip-country-lowcarbon-gauge" className="country-gauge-wrap">
              <TooltipLowCarbonGauge />
            </div>
            <div className="country-col-headline">{co2Sub(__('country-panel.lowcarbon'))}</div>
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
        {__('tooltips.noParserInfo')}
      </div>
    </div>
    <div id="exchange-tooltip" className="tooltip panel">
      {__('tooltips.crossborderexport')}
      :
      <br />
      <img className="from flag" alt="" />
      {' '}
      <span id="from" />
       → 
      <img className="to flag" alt="" />
      {' '}
      <span id="to" />
      : 
      <span id="flow" style={{ fontWeight: 'bold' }} />
      MW
      <br />
      <br />
      {co2Sub(__('tooltips.carbonintensityexport'))}
      :
      <br />
      <div className="emission-rect" />
      {' '}
      <span className="country-emission-intensity emission-intensity" />
      gCO
      <span className="sub">2</span>
      eq/kWh
    </div>
    <div id="price-tooltip" className="tooltip panel">
      <span className="value" />
      {' '}
      <span className="currency" />
      /MWh
    </div>
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
        {co2Sub(__('tooltips.withcarbonintensity'))}
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
    <div id="countrypanel-exchange-tooltip" className="tooltip panel">
      <span id="line1" />
      <br />
      <small>
        (
        <span id="exchange-proportion-detail" />
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
        {co2Sub(__('tooltips.withcarbonintensity'))}
        <br />
        <img className="country-exchange-source-flag flag" alt="" />
        {' '}
        <span className="country-exchange-source-name" />
        : 
        <div className="emission-rect" />
        {' '}
        <span className="emission-intensity" />
        gCO
        <span className="sub">2</span>
        eq/kWh
        <br />
      </span>
    </div>
    <div id="lowcarb-info-tooltip" className="tooltip panel">
      <span id="lowcarb-info-title" />
      <br />
      <small><span id="lowcarb-info-text" /></small>
      <br />
    </div>
  </React.Fragment>
);
