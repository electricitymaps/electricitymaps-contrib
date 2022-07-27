import React from 'react';
import styled from 'styled-components';
import { CSSTransition } from 'react-transition-group';

// TODO: add animation to logo to indicate loading

const Overlay = styled.div`
  background-image: url(${resolvePath('images/electricitymap-logo.svg')});
  background-position: 50% center, center center;
  background-repeat: no-repeat, no-repeat;
  background-size: 190px, 10rem;
  background-color: #fafafa;
  transition: opacity ${(props) => props.fadeTimeout}ms ease-in-out;
  z-index: 500;
  flex: 1 1 0;
`;

export default ({ fadeTimeout = 500, visible }) => (
  <CSSTransition in={visible} timeout={fadeTimeout} classNames="fade">
    <Overlay id="loading" fadeTimeout={fadeTimeout} />
  </CSSTransition>
);
