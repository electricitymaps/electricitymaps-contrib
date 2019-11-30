import React from 'react';

import { __ } from '../helpers/translation';

export default () => (
  <div className="prodcons-toggle-container">
    <div className="production-toggle">
      <div className="production-toggle-active-overlay" />
      <div className="production-toggle-item production">
        {__('tooltips.production')}
      </div>
      <div className="production-toggle-item consumption">
        {__('tooltips.consumption')}
      </div>
    </div>
    <div className="production-toggle-info">
      i
    </div>
    <div id="production-toggle-tooltip" className="layer-button-tooltip hidden">
      <div className="tooltip-container">
        <div className="tooltip-text">
          {' '}
          {__('tooltips.cpinfo')}
        </div>
        <div className="arrow" />
      </div>
    </div>
  </div>
);
