import React from 'react';
import { NavigationControl } from 'react-map-gl';
import styled, { css } from 'styled-components';

// override mapbox styling
const Wrapper = styled.div`
  border-radius: 6px;
  box-shadow: 0px 0px 10px 0px ${({ theme }) => theme.shadowColor};
  position: absolute;
  right: 16px;
  top: 69px;
  transition: box-shadow 0.4s;
  user-select: none;

  @media screen and (max-width: 767px) {
    top: 66px;
  }

  &:hover {
    box-shadow: 2px 0px 20px 0px ${({ theme }) => theme.shadowColorHovered};
  }

  .mapboxgl-ctrl {
    border-radius: 6px;
    box-shadow: none;
    background-color: ${({ theme }) => theme.background};
  }

  && button {
    width: 35px;
    height: 35px;
    background-size: 100% 100%;
    transition: background-color 0.4s;
  }
  && button + button {
    border-top-color: ${({ theme }) => theme.shadowColor};
  }

  ${({ theme }) =>
    theme.name.includes('dark') &&
    css`
      // Overriding the default SVGs to change fill
      .mapboxgl-ctrl button.mapboxgl-ctrl-zoom-in .mapboxgl-ctrl-icon {
        background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg width='29' height='29' xmlns='http://www.w3.org/2000/svg' fill='%23ccc'%3E%3Cpath d='M14.5 8.5c-.75 0-1.5.75-1.5 1.5v3h-3c-.75 0-1.5.75-1.5 1.5S9.25 16 10 16h3v3c0 .75.75 1.5 1.5 1.5S16 19.75 16 19v-3h3c.75 0 1.5-.75 1.5-1.5S19.75 13 19 13h-3v-3c0-.75-.75-1.5-1.5-1.5z'/%3E%3C/svg%3E");
      }
      .mapboxgl-ctrl button.mapboxgl-ctrl-zoom-out .mapboxgl-ctrl-icon {
        background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg width='29' height='29' xmlns='http://www.w3.org/2000/svg' fill='%23ccc'%3E%3Cpath d='M10 13c-.75 0-1.5.75-1.5 1.5S9.25 16 10 16h9c.75 0 1.5-.75 1.5-1.5S19.75 13 19 13h-9z'/%3E%3C/svg%3E");
      }
    `}
`;

// Note: the id property is being used by Cordova app
export const ZoomControls = () => (
  <Wrapper id="zoom-controls">
    <NavigationControl showCompass={false} zoomInLabel="" zoomOutLabel="" />
  </Wrapper>
);
