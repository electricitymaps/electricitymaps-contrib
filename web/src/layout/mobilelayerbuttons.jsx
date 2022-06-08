import React from 'react';
import styled from 'styled-components';
import { dispatchApplication } from '../store';

const Wrapper = styled.div`
  @media (min-width: 768px) {
    display: none;
  }
  position: absolute;
  top: 0;
  right: 0;
`;

export default () => {
  const openSettings = () => {
    dispatchApplication('settingsModalOpen', true);
  };

  return (
    <Wrapper>
      <button>info</button>
      <button onClick={openSettings}>SETTINGS</button>
    </Wrapper>
  );
};
