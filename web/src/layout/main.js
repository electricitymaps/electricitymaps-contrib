/* eslint-disable */
// TODO: remove once refactored

import React from 'react';
import { connect } from 'react-redux';

// Components
import CircularGauge from '../components/circulargauge';

// Layout
import Inner from './inner';

const { co2Sub } = require('../helpers/formatting');
const { __ } = require('../helpers/translation');

const TooltipLowCarbonGauge = connect(state => ({
  percentage: state.application.tooltipLowCarbonGaugePercentage,
}))(CircularGauge);
const TooltipRenewableGauge = connect(state => ({
  percentage: state.application.tooltipRenewableGaugePercentage,
}))(CircularGauge);

export default (props) => {
  return (
    <React.Fragment>
      <Inner />
      <div id="country-tooltip" className="tooltip panel">
        <div className="zone-name-header">
          <img id="country-flag" className="flag" /> <span id="country-name"></span>
        </div>
        <div className="zone-details">
          <div className="country-table-header-inner">
            <div className="country-col country-emission-intensity-wrap">
              <div id="country-emission-rect" className="country-col-box emission-rect emission-rect-overview">
                <div><span className="country-emission-intensity"></span>g</div>
              </div>
              <div className="country-col-headline">{ co2Sub(__('country-panel.carbonintensity')) }</div>
            </div>
            <div className="country-col country-lowcarbon-wrap">
              <div id="tooltip-country-lowcarbon-gauge" className="country-gauge-wrap">
                <TooltipLowCarbonGauge />
              </div>
              <div className="country-col-headline">{ co2Sub(__('country-panel.lowcarbon')) }</div>
              <div className="country-col-subtext"></div>
            </div>
            <div className="country-col country-renewable-wrap">
              <div id="tooltip-country-renewable-gauge" className="country-gauge-wrap">
                <TooltipRenewableGauge />
              </div>
              <div className="country-col-headline">{ __('country-panel.renewable') }</div>
            </div>
          </div>
        </div>
        <div className="temporary-outage-text">
          {        __('tooltips.temporaryDataOutage')  }
        </div>
        <div className="no-parser-text">
          {        __('tooltips.noParserInfo')  }
        </div>
      </div>
      <div id="exchange-tooltip" className="tooltip panel">
        { __('tooltips.crossborderexport') }:<br />
        <img className="from flag"></img> <span id="from"></span> → <img className="to flag"></img> <span id="to"></span>: <span id="flow" style={{ fontWeight: 'bold' }}></span> MW<br />
        <br />
        { co2Sub(__('tooltips.carbonintensityexport')) }:<br />
        <div className="emission-rect"></div> <span className="country-emission-intensity emission-intensity"></span> gCO<span className="sub">2</span>eq/kWh
      </div>
      <div id="price-tooltip" className="tooltip panel">
        <span className="value"></span> <span className="currency"></span>/MWh
      </div>
      <div id="countrypanel-production-tooltip" className="tooltip panel">
        <span id="line1"></span><br />
        <small>(<span id="production-proportion-detail"></span>)</small><br />
        <span className="production-visible">
          <br />
          { __('tooltips.utilizing') } <b><span id="capacity-factor"></span></b> { __('tooltips.ofinstalled') }<br />
          <small>(<span id="capacity-factor-detail"></span>)</small><br />
          <br />
          { co2Sub(__('tooltips.withcarbonintensity')) }<br />
          <div className="emission-rect"></div> <span className="emission-intensity"></span> gCO<span className="sub">2</span>eq/kWh <small>({ __('country-panel.source') }: <span className="emission-source"></span>)</small>
        </span>
      </div>
      <div id="countrypanel-exchange-tooltip" className="tooltip panel">
        <span id="line1"></span><br />
        <small>(<span id="exchange-proportion-detail"></span>)</small><br />
        <span className="production-visible">
          <br />
          { __('tooltips.utilizing') } <b><span id="capacity-factor"></span></b> { __('tooltips.ofinstalled') }<br />
          <small>(<span id="capacity-factor-detail"></span>)</small><br />
          <br />
          { co2Sub(__('tooltips.withcarbonintensity')) }<br />
          <img className="country-exchange-source-flag flag"></img> <span className="country-exchange-source-name"></span>: <div className="emission-rect"></div> <span className="emission-intensity"></span> gCO<span className="sub">2</span>eq/kWh<br />
        </span>
      </div>
      <div id="lowcarb-info-tooltip" className="tooltip panel">
        <span id="lowcarb-info-title"></span><br />
        <small><span id="lowcarb-info-text"></span></small><br />
      </div>
    </React.Fragment>
  );
}
