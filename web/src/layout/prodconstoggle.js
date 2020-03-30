import React from 'react';
import { connect } from 'react-redux';

import { __ } from '../helpers/translation';

// TODO: Move styles from styles.css to here

const mapStateToProps = state => ({
  electricityMixMode: state.application.electricityMixMode,
});

export default connect(mapStateToProps)(props => (
  <div className="prodcons-toggle-container">
    <div className="production-toggle">
      <div className={`production-toggle-item production ${props.electricityMixMode === 'production' ? 'production-toggle-active-overlay' : ''}`}>
        {__('tooltips.production')}
      </div>
      <div className={`production-toggle-item consumption ${props.electricityMixMode !== 'production' ? 'production-toggle-active-overlay' : ''}`}>
        {__('tooltips.consumption')}
      </div>
    </div>
    <div className="production-toggle-info">
      i
    </div>
    <div id="production-toggle-tooltip" className="layer-button-tooltip hidden">
      <div className="tooltip-container">
        <div className="tooltip-text" dangerouslySetInnerHTML={{ __html: __('tooltips.cpinfo') }} />
        <div className="arrow" />
      </div>
    </div>
  </div>
));
