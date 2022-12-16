import React from 'react';
import { useSelector } from 'react-redux';
import { Link as RouterLink } from 'react-router-dom';

import { useTranslation } from '../helpers/translation';
import { saveKey } from '../helpers/storage';
import { useWindEnabled, useSolarEnabled, useSnowEnabled, useSolarToggledLocation, useWindToggledLocation, useSnowToggledLocation } from '../hooks/router';
import { dispatchApplication } from '../store';

import LanguageSelect from '../components/languageselect';
import ButtonToggle from '../components/buttontoggle';
import { useTrackEvent } from '../hooks/tracking';
import styled from 'styled-components';
import { TIME } from '../helpers/constants';

const HiddenOnMobile = styled.div`
  @media screen and (max-width: 767px) {
    display: none;
  }
`;

export default () => {
  const { __ } = useTranslation();
  const windEnabled = useWindEnabled();
  const windToggledLocation = useWindToggledLocation();
  const windDataError = useSelector((state) => state.data.windDataError);
  const trackEvent = useTrackEvent();
  const solarEnabled = useSolarEnabled();
  const solarDataError = useSelector((state) => state.data.solarDataError);
  const solarToggledLocation = useSolarToggledLocation();

  const snowEnabled = useSnowEnabled();
  const snowDataError = useSelector((state) => state.data.snowDataError);
  const snowToggledLocation = useSnowToggledLocation();

  const brightModeEnabled = useSelector((state) => state.application.brightModeEnabled);

  const isWeatherEnabled = useSelector(
    (state) => state.application.selectedTimeAggregate === TIME.HOURLY && state.application.selectedZoneTimeIndex === 24
  );
  const toggleBrightMode = () => {
    dispatchApplication('brightModeEnabled', !brightModeEnabled);
    trackEvent(`Dark Mode ${brightModeEnabled ? 'Enabled' : 'Disabled'}`);
    saveKey('brightModeEnabled', !brightModeEnabled);
  };

  const Link = ({ to, hasError, children }) =>
    !hasError ? <RouterLink to={to}>{children}</RouterLink> : <div>{children}</div>;

  const getWeatherTranslateId = (weatherType, enabled, isWeatherEnabled) => {
    if (!isWeatherEnabled) {
      return 'tooltips.weatherDisabled';
    }

    return enabled ? `tooltips.hide${weatherType}Layer` : `tooltips.show${weatherType}Layer`;
  };

  return (
    <HiddenOnMobile>
      <div className={'layer-buttons-container'}>
        <LanguageSelect />
        <Link
          to={windToggledLocation}
          onClick={() => trackEvent(`Wind Layer ${!windEnabled ? 'Enabled' : 'Disabled'}`)}
          hasError={windDataError || !isWeatherEnabled}
        >
          <ButtonToggle
            active={windEnabled}
            tooltip={__(getWeatherTranslateId('Wind', windEnabled, isWeatherEnabled))}
            errorMessage={windDataError}
            ariaLabel={__(getWeatherTranslateId('Wind', solarEnabled, isWeatherEnabled))}
            icon="weather/wind"
            onChange={() => trackEvent(`Wind Layer ${!windEnabled ? 'Enabled' : 'Disabled'}`)}
          />
        </Link>
        <Link
          to={solarToggledLocation}
          onClick={() => trackEvent(`Solar Layer ${!solarEnabled ? 'Enabled' : 'Disabled'}`)}
          hasError={solarDataError || !isWeatherEnabled}
        >
          <ButtonToggle
            active={solarEnabled}
            tooltip={__(getWeatherTranslateId('Solar', solarEnabled, isWeatherEnabled))}
            errorMessage={solarDataError}
            ariaLabel={__(getWeatherTranslateId('Solar', solarEnabled, isWeatherEnabled))}
            icon="weather/sun"
            onChange={() => trackEvent(`Solar Layer ${!solarEnabled ? 'Enabled' : 'Disabled'}`)}
          />
        </Link>
        <Link
          to={snowToggledLocation}
          onClick={() => trackEvent(`Snow Layer ${!solarEnabled ? 'Enabled' : 'Disabled'}`)}
          hasError={snowDataError || !isWeatherEnabled}
        >
          <ButtonToggle
            active={snowEnabled}
            tooltip={__(getWeatherTranslateId('Snow', snowEnabled, isWeatherEnabled))}
            errorMessage={solarDataError}
            ariaLabel={__(getWeatherTranslateId('Snow', snowEnabled, isWeatherEnabled))}
            icon="weather/snow"
            onChange={() => trackEvent(`Snow Layer ${!snowEnabled ? 'Enabled' : 'Disabled'}`)}
          />
        </Link>
        <ButtonToggle
          active={brightModeEnabled}
          onChange={toggleBrightMode}
          tooltip={__('tooltips.toggleDarkMode')}
          ariaLabel={__('tooltips.toggleDarkMode')}
          icon="brightmode"
        />
      </div>
    </HiddenOnMobile>
  );
};
