import React from 'react';
import { useSelector } from 'react-redux';

import { __ } from '../helpers/translation';
import { saveKey } from '../helpers/storage';
import {
  useSolarEnabled,
  setSolarEnabled,
} from '../helpers/router';
import { dispatchApplication } from '../store';

import LanguageSelect from '../components/languageselect';
import ButtonToggle from '../components/buttontoggle';

export default () => {
  const solarEnabled = useSolarEnabled();
  const toggleSolar = () => {
    setSolarEnabled(!solarEnabled);
  };

  const brightModeEnabled = useSelector(state => state.application.brightModeEnabled);
  const toggleBrightMode = () => {
    dispatchApplication('brightModeEnabled', !brightModeEnabled);
    saveKey('brightModeEnabled', !brightModeEnabled);
  };

  return (
    <div className="layer-buttons-container">
      <LanguageSelect />
      <div>
        <button type="button" className="layer-button wind-button" />
        <div id="wind-layer-button-tooltip" className="layer-button-tooltip hidden">
          <div className="tooltip-container">
            <div className="tooltip-text">{__('tooltips.showWindLayer')}</div>
            <div className="arrow" />
          </div>
        </div>
      </div>
      <ButtonToggle
        active={solarEnabled}
        onChange={toggleSolar}
        tooltip={__(solarEnabled ? 'tooltips.hideSolarLayer' : 'tooltips.showSolarLayer')}
        icon="weather/sun"
      />
      <ButtonToggle
        active={brightModeEnabled}
        onChange={toggleBrightMode}
        tooltip={__('tooltips.toggleDarkMode')}
        icon="brightmode"
      />
    </div>
  );
};
