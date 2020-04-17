import React from 'react';
import { useSelector } from 'react-redux';

import { __ } from '../helpers/translation';
import { saveKey } from '../helpers/storage';
import {
  useWindEnabled,
  setWindEnabled,
  useSolarEnabled,
  setSolarEnabled,
} from '../helpers/router';
import { dispatchApplication } from '../store';

import LanguageSelect from '../components/languageselect';
import ButtonToggle from '../components/buttontoggle';

export default () => {
  const windEnabled = useWindEnabled();
  const toggleWind = () => {
    setWindEnabled(!windEnabled);
  };

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
      <ButtonToggle
        active={windEnabled}
        onChange={toggleWind}
        tooltip={__(windEnabled ? 'tooltips.hideWindLayer' : 'tooltips.showWindLayer')}
        icon="weather/wind"
      />
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
