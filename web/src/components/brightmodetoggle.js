import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { noop } from 'lodash';

// Modules
import { __ } from '../helpers/translation';
import { saveKey } from '../helpers/storage';
import { dispatchApplication } from '../store';

export default () => {
  const isMobile = useSelector(state => state.application.isMobile);

  const brightModeEnabled = useSelector(state => state.application.brightModeEnabled);
  const toggleBrightMode = () => {
    dispatchApplication('brightModeEnabled', !brightModeEnabled);
    saveKey('brightModeEnabled', !brightModeEnabled);
  };

  const [tooltipVisible, setTooltipVisible] = useState(false);
  const showTooltip = () => { setTooltipVisible(true); };
  const hideTooltip = () => { setTooltipVisible(false); };

  return (
    <div>
      <button
        type="button"
        className={`layer-button brightmode-button ${brightModeEnabled ? 'active' : ''}`}
        onFocus={isMobile ? noop : showTooltip}
        onMouseOver={isMobile ? noop : showTooltip}
        onMouseOut={isMobile ? noop : hideTooltip}
        onBlur={isMobile ? noop : hideTooltip}
        onClick={toggleBrightMode}
      />
      {tooltipVisible && (
        <div className="layer-button-tooltip">
          <div className="tooltip-container">
            <div className="tooltip-text">{__('tooltips.toggleDarkMode')}</div>
            <div className="arrow" />
          </div>
        </div>
      )}
    </div>
  );
};
