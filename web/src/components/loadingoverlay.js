import React from 'react';
import styled, { createGlobalStyle } from 'styled-components';
import { CSSTransition } from 'react-transition-group';

// TODO: Pull this up the DOM hierarchy.
const FadeAnimationDefinition = createGlobalStyle`
  .fade-enter { opacity: 0; }
  .fade-enter-active { opacity: 1; }
  .fade-exit { opacity: 1; }
  .fade-exit-active { opacity: 0; }
  .fade-exit-done { display: none; }
`;

const Overlay = styled.div`
  background-image: url('../images/loading/loading64_FA.gif'), url('../images/loading/electricitymap-text.svg');
  background-position: calc(50% - 64px) center , center center;
  background-repeat: no-repeat, no-repeat;
  background-size: 36px , 10rem;
  background-color: #fafafa;
  width: 100%;
  height: 100%;
  display: inline-block;
  position: fixed;
  top: 0;
  transition: opacity ${props => props.fadeTimeout}ms ease-in-out;
  z-index: 500;
`;

export default ({ fadeTimeout = 500, visible }) => (
  <React.Fragment>
    <FadeAnimationDefinition />
    <CSSTransition in={visible} timeout={fadeTimeout} classNames="fade">
      <Overlay fadeTimeout={fadeTimeout} />
    </CSSTransition>
  </React.Fragment>
);
