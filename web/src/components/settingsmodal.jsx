import React, { useState } from 'react';
import { useTranslation } from '../helpers/translation';
import { dispatchApplication } from '../store';
import { useTrackEvent } from '../hooks/tracking';
import { saveKey } from '../helpers/storage';
import { useWindEnabled, useSolarEnabled, useSolarToggledLocation, useWindToggledLocation } from '../hooks/router';
import { LANGUAGE_NAMES } from '../helpers/constants';
import Toggle from './toggle';

import styled from 'styled-components';
import { useSelector } from 'react-redux';
import { Link } from 'react-router-dom';

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
  margin-top: -6px;
  list-style: none;
  box-shadow: 0px 0px 13px rgba(0, 0, 0, 0.12);
  overflow: scroll;
  max-height: 300px;
  li {
    padding: 8px;
    cursor: pointer;
    &:hover {
      background-color: #f5f5f5;
    }
  }
`;

const LanguageSelect = ({ isOpen, onSelect }) => {
  if (!isOpen) {
    return null;
  }

  return (
    <StyledLanguageSelectWrapper>
      {Object.entries(LANGUAGE_NAMES).map(([key, language]) => (
        <li key={key} onClick={() => onSelect(key)}>
          {language}
        </li>
      ))}
    </StyledLanguageSelectWrapper>
  );
};

const SettingButton = ({ text, link, active, onToggle, ...rest }) => {
  const bgColor = active ? '#fff' : '#fff';
  const textColor = active ? '#000' : '#999';

  const props = {
    ...rest,
    bgColor,
    textColor,
    onClick: onToggle,
    iconSize: 18,
  };

  if (link && !rest.disabled) {
    props.as = Link;
    props.to = link;
  }

  return <Button {...props}>{text}</Button>;
};

const SettingsView = () => {
  const { __, i18n } = useTranslation();
  const [languageSelectOpen, setLanguageSelectOpen] = useState(false);

  const windEnabled = useWindEnabled();
  const windToggledLocation = useWindToggledLocation();
  const brightModeEnabled = useSelector((state) => state.application.brightModeEnabled);
  const windDataError = useSelector((state) => state.data.windDataError);
  const solarDataError = useSelector((state) => state.data.solarDataError);

  const solarEnabled = useSolarEnabled();
  const solarToggledLocation = useSolarToggledLocation();

  const electricityMixMode = useSelector((state) => state.application.electricityMixMode);
  const colorBlindModeEnabled = useSelector((state) => state.application.colorBlindModeEnabled);

  const handleLanguageChange = (language) => {
    i18n.changeLanguage(language);
    setLanguageSelectOpen(false);
  };
  const toggleSetting = (name, currentValue) => {
    dispatchApplication(name, !currentValue);
    saveKey(name, !currentValue);
  };

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
        tooltipStyle={{ width: 250, top: 110, zIndex: 9 }}
      />
      <SettingsWrapper>
        <SettingButton
          active
          icon="language"
          text={__('tooltips.selectLanguage')}
          onToggle={() => setLanguageSelectOpen(!languageSelectOpen)}
        />
        <LanguageSelect isOpen={languageSelectOpen} onSelect={handleLanguageChange} />
        <LayerErrorMessage>{windDataError}</LayerErrorMessage>
        <SettingButton
          link={windToggledLocation}
          icon="wind"
          text={__(windEnabled ? 'tooltips.hideWindLayer' : 'tooltips.showWindLayer')}
          active={windEnabled}
          disabled={windDataError}
        />
        <LayerErrorMessage>{solarDataError}</LayerErrorMessage>
        <SettingButton
          link={solarToggledLocation}
          icon="sun"
          text={__(solarEnabled ? 'tooltips.hideSolarLayer' : 'tooltips.showSolarLayer')}
          active={solarEnabled}
          disabled={solarDataError}
        />
        <SettingButton
          icon="dark-mode"
          text={__('tooltips.toggleDarkMode')}
          active={!brightModeEnabled}
          onToggle={() => toggleSetting('brightModeEnabled', brightModeEnabled)}
        />
        <SettingButton
          icon="low-vision"
          text={__('legends.colorblindmode')}
          active={colorBlindModeEnabled}
          onToggle={() => toggleSetting('colorBlindModeEnabled', colorBlindModeEnabled)}
        />
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
