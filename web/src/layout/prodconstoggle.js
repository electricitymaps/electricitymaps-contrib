import React, { useState } from 'react';
import { connect } from 'react-redux';
import { findIndex, isEmpty } from 'lodash';

import { __ } from '../helpers/translation';
import { dispatchApplication } from '../store';

// TODO: Move styles from styles.css to here

const Toggle = ({
  infoHTML,
  onChange,
  options,
  value,
}) => {
  const [tooltipVisible, setTooltipVisible] = useState(false);

  const activeIndex = findIndex(options, { value });
  const nextIndex = (activeIndex + 1) % options.length;
  const nextValue = options[nextIndex].value;

  return (
    <div className="prodcons-toggle-container">
      <div className="production-toggle" onClick={() => onChange(nextValue)}>
        {options.map(o => (
          <div key={o.value} className={`production-toggle-item production ${o.value === value ? 'production-toggle-active-overlay' : ''}`}>
            {o.label}
          </div>
        ))}
      </div>
      {!isEmpty(infoHTML) && (
        <React.Fragment>
          <div className="production-toggle-info" onClick={() => setTooltipVisible(!tooltipVisible)}>i</div>
          <div id="production-toggle-tooltip" className={`layer-button-tooltip ${tooltipVisible ? '' : 'hidden'}`}>
            <div className="tooltip-text" dangerouslySetInnerHTML={{ __html: infoHTML }} />
          </div>
        </React.Fragment>
      )}
    </div>
  );
};

const mapStateToProps = state => ({
  electricityMixMode: state.application.electricityMixMode,
});

const ProdConsToggle = ({ electricityMixMode }) => (
  <Toggle
    infoHTML={__('tooltips.cpinfo')}
    onChange={value => dispatchApplication('electricityMixMode', value)}
    options={[
      { value: 'production', label: __('tooltips.production') },
      { value: 'consumption', label: __('tooltips.consumption') },
    ]}
    value={electricityMixMode}
  />
);

export default connect(mapStateToProps)(ProdConsToggle);
