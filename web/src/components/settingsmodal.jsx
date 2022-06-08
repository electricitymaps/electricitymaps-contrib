import React from 'react';
import { useTranslation } from '../helpers/translation';
import { saveKey } from '../helpers/storage';
import { dispatchApplication } from '../store';
import { useTrackEvent } from '../hooks/tracking';

import { Link as RouterLink } from 'react-router-dom';

import Icon from './icon';
import styled from 'styled-components';
import Toggle from './toggle';
import { useSelector } from 'react-redux';
import { useWindEnabled, useSolarEnabled, useSolarToggledLocation, useWindToggledLocation } from '../hooks/router';
import LanguageSelect from '../components/languageselect';
import Modal from './modal';

const Link = ({ to, hasError, children }) =>
  !hasError ? <RouterLink to={to}>{children}</RouterLink> : <div>{children}</div>;

const ModalTitle = styled.h2`
  &&& {
    font-weight: bold;
    margin-bottom: 1.5rem;
  }
`;

const Settings = styled.div`
  margin-top: 1rem;
`;

// button with icon
const StyledIcon = styled(Icon)`
  fill: ${(props) => (props.active ? 'green' : '#000')};
  margin-right: 2px;
`;

const StyledSettingButton = styled.button`
  background: ${(props) => props.bgColor || '#fff'};
  color: ${(props) => props.textColor || '#000'};
  opacity: ${(props) => (props.active ? 1 : 0.5)};
  font-family: 'Open Sans', sans-serif;
  border-radius: 100px;
  width: 232px;
  height: 50px;
  box-shadow: 0px 0px 13px rgba(0, 0, 0, 0.12);
  border: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  margin: 12px 6px;
  transition: all 0.2s ease-in-out;
  &:hover {
    cursor: pointer;
    box-shadow: 0px 0px 23px rgba(0, 0, 0, 0.2);
  }
`;

const SettingButton = ({ icon, children, ...rest }) => (
  <StyledSettingButton {...rest}>
    {icon && <StyledIcon iconName={icon} />}
    {children}
  </StyledSettingButton>
);

const SettingsContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const SettingsView = () => {
  const windEnabled = useWindEnabled();
  const windToggledLocation = useWindToggledLocation();
  const windDataError = useSelector((state) => state.data.windDataError);

  const solarEnabled = useSolarEnabled();
  const solarDataError = useSelector((state) => state.data.solarDataError);
  const solarToggledLocation = useSolarToggledLocation();

  const electricityMixMode = useSelector((state) => state.application.electricityMixMode);
  const brightModeEnabled = useSelector((state) => state.application.brightModeEnabled);
  const { __ } = useTranslation();

  const toggleSetting = (name, setting) => {
    dispatchApplication(name, !setting);
    saveKey(name, !setting);
  };

  return (
    <SettingsContainer>
      <ModalTitle>Settings</ModalTitle>
      <Toggle
        infoHTML={__('tooltips.cpinfo')}
        onChange={(value) => dispatchApplication('electricityMixMode', value)}
        options={[
          { value: 'production', label: __('tooltips.production') },
          { value: 'consumption', label: __('tooltips.consumption') },
        ]}
        value={electricityMixMode}
      />
      <Settings>
        <LanguageSelect />
        <Link to={windToggledLocation} hasError={windDataError}>
          <SettingButton active={windEnabled} icon="wind" onClick={() => {}}>
            {__(windEnabled ? 'tooltips.hideWindLayer' : 'tooltips.showWindLayer')}
          </SettingButton>
        </Link>
        <Link to={solarToggledLocation} hasError={solarDataError}>
          <SettingButton active={solarEnabled} icon="solar" onClick={() => {}}>
            {__(solarEnabled ? 'tooltips.hideSolarLayer' : 'tooltips.showSolarLayer')}
          </SettingButton>
        </Link>

        <SettingButton
          active={brightModeEnabled}
          onClick={() => toggleSetting('brightModeEnabled', brightModeEnabled)}
          icon="brightmode"
        >
          {__('tooltips.toggleDarkMode')}
        </SettingButton>
      </Settings>
    </SettingsContainer>
  );
};

const views = [
  {
    renderContent: (__) => <SettingsView />,
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

  return <Modal visible={modalOpen} onModalShown={handleShown} onDismiss={handleDismiss} views={views} />;
};

export default SettingsModal;
