import React from 'react';
import styled from 'styled-components';
import { CSSTransition } from 'react-transition-group';

const Wrapper = styled.div`
  display: flex;
  z-index: 500;
  flex: 1;
  transition: opacity ${(props) => props.fadeTimeout}ms ease-in-out;
`;
const BackgroundColoringBox = styled.div`
  display: flex;
  flex: 1;
  justify-content: center;
  background-color: ${({ theme }) => (theme.name === 'dark' ? '#000' : theme.background)};
`;

const BouncingLogo = styled.div`
  background-image: url(${resolvePath('images/loading/loading64_FA.gif')});
  background-repeat: no-repeat;
  background-position: center;
  background-size: 36px;
  filter: invert(${({ theme }) => (theme.name === 'dark' ? 100 : 0)}%);
  width: 36px;
`;

const Overlay = styled.div`
  background-image: url(${resolvePath('images/loading/electricitymap-text.svg')});
  background-position: 100% center;
  background-repeat: no-repeat;
  background-size: 10rem;
  filter: invert(${({ theme }) => (theme.name === 'dark' ? 100 : 0)}%);
  width: 8rem;
`;

export default ({ fadeTimeout = 500, visible }) => {
  return (
    <CSSTransition in={visible} timeout={fadeTimeout} classNames="fade">
      <Wrapper id="loading" fadeTimeout={fadeTimeout}>
        <BackgroundColoringBox>
          <BouncingLogo />
          <Overlay />
        </BackgroundColoringBox>
      </Wrapper>
    </CSSTransition>
  );
};
