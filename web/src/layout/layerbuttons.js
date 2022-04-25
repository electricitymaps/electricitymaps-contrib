import React from 'react';
import { useSelector } from 'react-redux';
import { Link as RouterLink } from 'react-router-dom';

import { useTranslation } from '../helpers/translation';
import { saveKey } from '../helpers/storage';
import {
  useWindEnabled,
  useSolarEnabled,
  useSolarToggledLocation,
  useWindToggledLocation,
  useAggregateToggledLocation,
  useAggregateEnabled,
  useSearchParams
} from '../hooks/router';
import { dispatchApplication } from '../store';

import LanguageSelect from '../components/languageselect';
import ButtonToggle from '../components/buttontoggle';

export default () => {
  const { __ } = useTranslation();
  const windEnabled = useWindEnabled();
  const windToggledLocation = useWindToggledLocation();
  const windDataError = useSelector(state => state.data.windDataError);

  const solarEnabled = useSolarEnabled();
  const solarDataError = useSelector(state => state.data.solarDataError);
  const solarToggledLocation = useSolarToggledLocation();

  const aggregateEnabled = useAggregateEnabled();
  const aggregateToggledLocation = useAggregateToggledLocation();
  const searchParams = useSearchParams();

  const brightModeEnabled = useSelector(state => state.application.brightModeEnabled);
  const toggleBrightMode = () => {
    dispatchApplication('brightModeEnabled', !brightModeEnabled);
    saveKey('brightModeEnabled', !brightModeEnabled);
  };

  const toggleAggregate = () => {
    if (aggregateEnabled) {
      window.location.href = "http://localhost:8000/map?aggregate=false"
    } else {
      window.location.href = "http://localhost:8000/map?aggregate=true"
    }
    
  }

  const Link = ({ to, hasError, children }) =>
  !hasError ? <RouterLink to={to}>{children}</RouterLink> : <div>{children}</div>;

  return (
    <div className="layer-buttons-container">
      <LanguageSelect />
      <Link to={windToggledLocation} hasError={windDataError}>
        <ButtonToggle
          active={windEnabled}
          tooltip={__(windEnabled ? 'tooltips.hideWindLayer' : 'tooltips.showWindLayer')}
          errorMessage={windDataError}
          ariaLabel={__(windEnabled ? 'tooltips.hideWindLayer' : 'tooltips.showWindLayer')}
          icon="weather/wind"
        />
      </Link>
      <Link to={solarToggledLocation} hasError={solarDataError}>
        <ButtonToggle
          active={solarEnabled}
          tooltip={__(solarEnabled ? 'tooltips.hideSolarLayer' : 'tooltips.showSolarLayer')}
          errorMessage={solarDataError}
          ariaLabel={__(solarEnabled ? 'tooltips.hideSolarLayer' : 'tooltips.showSolarLayer')}
          icon="weather/sun"
        />
      </Link>
      <ButtonToggle
        active={brightModeEnabled}
        onChange={toggleBrightMode}
        tooltip={__('tooltips.toggleDarkMode')}
        ariaLabel={__('tooltips.toggleDarkMode')}
        icon="brightmode"
        />
        <ButtonToggle
          active={aggregateEnabled}
          onChange={toggleAggregate}
          tooltip={__('tooltips.toggleAggregate')}
          ariaLabel={__('tooltips.toggleAggregate')}
          icon="agg"
        />
    </div>
  );
};
