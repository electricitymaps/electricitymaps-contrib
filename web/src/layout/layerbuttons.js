import React, { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { Link } from 'react-router-dom';

import { __ } from '../helpers/translation';
import { saveKey } from '../helpers/storage';
import {
  useWindEnabled,
  useSolarEnabled,
  useSolarToggledLocation,
  useWindToggledLocation,
} from '../helpers/router';
import { dispatchApplication } from '../store';

import LanguageSelect from '../components/languageselect';
import ButtonToggle from '../components/buttontoggle';

export default () => {
  const windEnabled = useWindEnabled();
  const windToggledLocation = useWindToggledLocation();

  const solarEnabled = useSolarEnabled();
  const solarToggledLocation = useSolarToggledLocation();

  const brightModeEnabled = useSelector(state => state.application.brightModeEnabled);
  const toggleBrightMode = () => {
    dispatchApplication('brightModeEnabled', !brightModeEnabled);
    saveKey('brightModeEnabled', !brightModeEnabled);
  };

  return (
    <div className="layer-buttons-container">
      <LanguageSelect />
      <Link to={windToggledLocation}>
        <ButtonToggle
          active={windEnabled}
          tooltip={__(windEnabled ? 'tooltips.hideWindLayer' : 'tooltips.showWindLayer')}
          icon="weather/wind"
        />
      </Link>
      <Link to={solarToggledLocation}>
        <ButtonToggle
          active={solarEnabled}
          tooltip={__(solarEnabled ? 'tooltips.hideSolarLayer' : 'tooltips.showSolarLayer')}
          icon="weather/sun"
        />
      </Link>
      <ButtonToggle
        active={brightModeEnabled}
        onChange={toggleBrightMode}
        tooltip={__('tooltips.toggleDarkMode')}
        icon="brightmode"
      />
    </div>
  );
};
