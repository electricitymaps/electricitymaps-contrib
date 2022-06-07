/* eslint-disable */ // TODO: Remove this
import React from 'react';
import { useTranslation } from '../helpers/translation';
import { saveKey } from '../helpers/storage';
import { dispatchApplication } from '../store';
import { useTrackEvent } from '../hooks/tracking';
import { useSearchParams } from '../hooks/router';

import { Link as RouterLink } from 'react-router-dom';

import Icon from './icon';
import { useToggle } from '../hooks/utils';
import styled from 'styled-components';
import Toggle from './toggle';
import { useSelector } from 'react-redux';
import { useWindEnabled, useSolarEnabled, useSolarToggledLocation, useWindToggledLocation } from '../hooks/router';
import LanguageSelect from '../components/languageselect';
import ButtonToggle from '../components/buttontoggle';
import Modal from './modal';

const Link = ({ to, hasError, children }) =>
  !hasError ? <RouterLink to={to}>{children}</RouterLink> : <div>{children}</div>;

// button with icon
const StyledIcon = styled(Icon)`
  fill: ${(props) => (props.active ? 'green' : '#000')};
  margin-right: 2px;
`;

const StyledSettingButton = styled.button`
  background: ${(props) => props.bgColor || '#fff'};
  color: ${(props) => props.textColor || '#000'};
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
  margin: 6px;
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

const StyledModal = styled.div`
  && {
    width: 80%;
  }
`;

const SettingsView = ({ onDismiss }) => {
  // TODO: Check isMobile from state
  const [isVisible, setIsVisible] = useToggle(true);
  const [windEnabled, setWindEnabled] = useToggle(false);
  const electricityMixMode = useSelector((state) => state.application.electricityMixMode);
  const brightModeEnabled = useSelector((state) => state.application.brightModeEnabled);
  //const windEnabled = useWindEnabled();
  const windToggledLocation = useWindToggledLocation();
  const windDataError = useSelector((state) => state.data.windDataError);
  const { __ } = useTranslation();

  const toggleSetting = (name, setting) => {
    dispatchApplication(name, !setting);
    saveKey(name, !setting);
  };

  //
  return (
    <SettingsContainer className="controls-container">
      <Toggle
        infoHTML={__('tooltips.cpinfo')}
        onChange={(value) => dispatchApplication('electricityMixMode', value)}
        options={[
          { value: 'production', label: __('tooltips.production') },
          { value: 'consumption', label: __('tooltips.consumption') },
        ]}
        value={electricityMixMode}
      />
      <SettingButton active={windEnabled} onClick={setWindEnabled} icon="wind">
        {__(windEnabled ? 'tooltips.hideWindLayer' : 'tooltips.showWindLayer')}
      </SettingButton>
      <SettingButton textColor={brightModeEnabled ? 'rgba(0,0,0,.5)' : '#000'} icon="brightmode">
        Show wind layer
      </SettingButton>
      <SettingButton bgColor="#44AB60" textColor="#fff" icon="brightmode">
        {__('tooltips.toggleDarkMode')}
      </SettingButton>
      <SettingButton bgColor="#04275C" textColor="#fff">
        Open Source
      </SettingButton>
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
    console.log('dismiss pls');
    dispatchApplication('settingsModalOpen', false);
  };

  const handleShown = () => {
    trackEvent('Onboarding Shown');
  };

  return <Modal visible={modalOpen} onModalShown={handleShown} onDismiss={handleDismiss} views={views} />;
};

export default SettingsModal;
