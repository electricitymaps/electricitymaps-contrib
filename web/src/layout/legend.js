import React from 'react';

// Modules
import { __ } from '../helpers/translation';

const { co2Sub } = require('../helpers/formatting');

export default () => (
  <div className="floating-legend-container">
    <div className="floating-legend-mobile-header">
      <span>{__('misc.legend')}</span>
      <i className="material-icons toggle-legend-button up">call_made</i>
      <i className="material-icons toggle-legend-button down visible">call_received</i>
    </div>
    <div className="wind-potential-legend floating-legend">
      <div className="legend-header">
        {__('legends.windpotential')}
        {' '}
        <small>(m/s)</small>
      </div>
      <svg className="wind-potential-bar potential-bar colorbar" />
    </div>
    <div className="solar-potential-legend floating-legend">
      <div className="legend-header">
        {__('legends.solarpotential')}
        {' '}
        <small>
          (W/m
          <span className="sup">2</span>
          )
        </small>
      </div>
      <svg className="solar-potential-bar potential-bar colorbar" />
    </div>
    <div className="co2-legend floating-legend">
      <div className="legend-header">
        {co2Sub(__('legends.carbonintensity'))}
        {' '}
        <small>
          (gCO
          <span className="sub">2</span>
          eq/kWh)
        </small>
      </div>
      <svg className="co2-colorbar colorbar potential-bar" />
    </div>
  </div>
);
