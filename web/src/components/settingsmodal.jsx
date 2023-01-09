import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { useTranslation } from '../helpers/translation';
import { dispatchApplication } from '../store';
import { useTrackEvent } from '../hooks/tracking';
import { saveKey } from '../helpers/storage';
import {
  useWindEnabled,
  useSolarEnabled,
  useSolarToggledLocation,
  useWindToggledLocation,
  useAggregatesToggle,
  useAggregatesEnabled,
} from '../hooks/router';
import { LANGUAGE_NAMES } from '../helpers/constants';

import Toggle from './toggle';

import styled from 'styled-components';
import { useSelector } from 'react-redux';

import Modal from './modal';
import { Button } from './button';

const InfoContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  p {
    margin-top: 0;
  }
`;

const SettingsWrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  > * {
    margin-bottom: 0;
    padding: 0 8px;
  }
`;
const LayerErrorMessage = styled.span`
  color: red;
  font-style: italic;
  font-size: 0.8rem;
`;

const StyledLanguageSelectWrapper = styled.ul`
  position: absolute;
  background-color: #fff;
  border-radius: 6px;
  width: 232px;
  margin: 0;
  padding: 0;
  list-style: none;
  box-shadow: 0px 0px 13px rgba(0, 0, 0, 0.12);
  overflow: scroll;
  max-height: 300px;

  button {
    width: 100%;
    background: transparent;
    border: 0;
    padding: 8px;
    cursor: pointer;
    &:hover {
      background-color: #f5f5f5;
    }
  }
`;

const SettingButton = styled(Button).attrs({
  iconSize: 18,
})`
  color: ${(props) => (props.active ? '#000' : '#999')};
`;

const LanguageSelect = ({ isOpen, onSelect }) => {
  if (!isOpen) {
    return null;
  }

  return (
    <StyledLanguageSelectWrapper>
      {Object.entries(LANGUAGE_NAMES).map(([key, language]) => (
        <li key={key}>
          <button onClick={() => onSelect(key)}>{language}</button>
        </li>
      ))}
    </StyledLanguageSelectWrapper>
  );
};

const SettingsView = () => {
  const { __, i18n } = useTranslation();
  const [languageSelectOpen, setLanguageSelectOpen] = useState(false);

  const windEnabled = useWindEnabled();
  const windToggledLocation = useWindToggledLocation();
  const windDataError = useSelector((state) => state.data.windDataError);
  const showWindErrorMessage = windEnabled && windDataError;

  const solarEnabled = useSolarEnabled();
  const solarToggledLocation = useSolarToggledLocation();
  const solarDataError = useSelector((state) => state.data.solarDataError);
  const showSolarErrorMessage = solarEnabled && solarDataError;

  const electricityMixMode = useSelector((state) => state.application.electricityMixMode);
  const colorBlindModeEnabled = useSelector((state) => state.application.colorBlindModeEnabled);
  const brightModeEnabled = useSelector((state) => state.application.brightModeEnabled);

  const handleLanguageChange = (language) => {
    i18n.changeLanguage(language);
    setLanguageSelectOpen(false);
  };
  const toggleSetting = (name, currentValue) => {
    dispatchApplication(name, !currentValue);
    saveKey(name, !currentValue);
  };

  const history = useHistory();
  const toggleAggregates = useAggregatesToggle();
  const isAggregated = useAggregatesEnabled() ? 'country' : 'zone';

  return (
    <InfoContainer>
      <Toggle
        infoHTML={__('tooltips.cpinfo')}
        onChange={(value) => dispatchApplication('electricityMixMode', value)}
        options={[
          { value: 'production', label: __('tooltips.production') },
          { value: 'consumption', label: __('tooltips.consumption') },
        ]}
        value={electricityMixMode}
        tooltipStyle={{ width: 250, top: 110, zIndex: 99 }}
      />

      <Toggle
        infoHTML={__('tooltips.aggregateinfo')}
        onChange={(value) => value !== isAggregated && history.push(toggleAggregates)}
        options={[
          { value: 'country', label: __('aggregateButtons.country') },
          { value: 'zone', label: __('aggregateButtons.zone') },
        ]}
        value={isAggregated}
        tooltipStyle={{ width: 250, top: 146, zIndex: 99 }}
      />

      <SettingsWrapper>
        <SettingButton active icon="language" onClick={() => setLanguageSelectOpen(!languageSelectOpen)}>
          {__('tooltips.selectLanguage')}
        </SettingButton>

        <LanguageSelect isOpen={languageSelectOpen} onSelect={handleLanguageChange} />

        <SettingButton to={windToggledLocation} icon="wind" active={windEnabled} disabled={windDataError}>
          {__(windEnabled ? 'tooltips.hideWindLayer' : 'tooltips.showWindLayer')}
        </SettingButton>
        {showWindErrorMessage && <LayerErrorMessage>{windDataError}</LayerErrorMessage>}

        <SettingButton to={solarToggledLocation} icon="sun" active={solarEnabled} disabled={solarDataError}>
          {__(solarEnabled ? 'tooltips.hideSolarLayer' : 'tooltips.showSolarLayer')}
        </SettingButton>
        {showSolarErrorMessage && <LayerErrorMessage>{solarDataError}</LayerErrorMessage>}

        <SettingButton
          icon="dark-mode"
          active={!brightModeEnabled}
          onClick={() => toggleSetting('brightModeEnabled', brightModeEnabled)}
        >
          {__('tooltips.toggleDarkMode')}
        </SettingButton>

        <SettingButton
          icon="low-vision"
          active={colorBlindModeEnabled}
          onClick={() => toggleSetting('colorBlindModeEnabled', colorBlindModeEnabled)}
        >
          {__('legends.colorblindmode')}
        </SettingButton>
      </SettingsWrapper>
    </InfoContainer>
  );
};

const views = [
  {
    title: (__) => __('settings-modal.title'),
    renderContent: () => <SettingsView />,
  },
];

const SettingsModal = () => {
  const modalOpen = useSelector((state) => state.application.settingsModalOpen);
  const trackEvent = useTrackEvent();

  const handleDismiss = () => {
    dispatchApplication('settingsModalOpen', false);
  };

  const handleShown = () => {
    trackEvent('Settings Modal Shown');
  };

  return (
    <Modal
      modalName={'settings'}
      visible={modalOpen}
      onModalShown={handleShown}
      onDismiss={handleDismiss}
      views={views}
    />
  );
};

export default SettingsModal;
