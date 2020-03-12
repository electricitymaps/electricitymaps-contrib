import React from 'react';

// Components
import CountryPanelExchangeTooltip from '../components/tooltips/countrypanelexchangetooltip';
import LowCarbonInfoTooltip from '../components/tooltips/lowcarboninfotooltip';
import MapCountryTooltip from '../components/tooltips/mapcountrytooltip';
import MapExchangeTooltip from '../components/tooltips/mapexchangetooltip';
import PriceTooltip from '../components/tooltips/pricetooltip';

const { co2Sub } = require('../helpers/formatting');
const { __ } = require('../helpers/translation');

export default () => (
  <React.Fragment>
    <MapCountryTooltip />
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
