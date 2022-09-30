import React from 'react';
import styled from 'styled-components';

import { CSSTransition } from 'react-transition-group';

// TODO: add animation to logo to indicate loading
const Overlay = styled.div`
  background-image: url(${resolvePath('images/electricitymap-loading.svg')});
  background-position: 50% center, center center;
  background-repeat: no-repeat, no-repeat;
  background-size: 190px, 10rem;
  background-color: #fafafa;
  transition: opacity ${(props) => (props as any).fadeTimeout}ms ease-in-out;
  z-index: 500;
  flex: 1 1 0;
`;

export default ({ fadeTimeout = 500, visible }: any) => (
  <CSSTransition in={visible} timeout={fadeTimeout} classNames="fade">
    {/* @ts-expect-error TS(2769): No overload matches this call. */}
    <Overlay id="loading" fadeTimeout={fadeTimeout} />
  </CSSTransition>
);
