import React from 'react';
import styled from 'styled-components';
import { dispatchApplication } from '../store';
import { Button } from './button';

const Wrapper = styled.div`
  @media (min-width: 768px) {
    display: none;
  }
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
`;

const ActionButton = styled(Button)`
  &:first-child {
    margin-right: 4px;
  }
`;

export default () => {
  const openInfoModal = () => dispatchApplication('infoModalOpen', true);
  const openSettingsModal = () => dispatchApplication('settingsModalOpen', true);

  return (
    <Wrapper>
      <ActionButton aria-label="open info modal" iconSize={18} icon="info" onClick={openInfoModal} />
      <ActionButton aria-label="open settings modal" iconSize={18} icon="sliders" onClick={openSettingsModal} />
    </Wrapper>
  );
};
