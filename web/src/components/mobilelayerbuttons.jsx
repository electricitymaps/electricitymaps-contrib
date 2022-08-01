import React from 'react';
import styled from 'styled-components';
import { dispatchApplication } from '../store';
import { Button } from './button';

const Wrapper = styled.div`
  @media (min-width: 768px) {
    display: none;
  }
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;

  /* iOS Safari 11.2, Safari 11 */
  top: constant(safe-area-inset-top, 10px);

  /* iOS Safari 11.4+, Safari 11.1+, Chrome 69+, Opera 56+ */
  top: env(safe-area-inset-top, 10px);
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
