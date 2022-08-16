import React from 'react';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'reac... Remove this comment to see the full error message
import { NavigationControl } from 'react-map-gl';
import styled from 'styled-components';

import { useTranslation } from '../helpers/translation';

// override mapbox styling
const Wrapper = styled.div`
  border-radius: 6px;
  box-shadow: 0px 0px 10px 0px rgba(0, 0, 0, 0.15);
  position: absolute;
  right: 16px;
  top: 69px;
  transition: box-shadow 0.4s;
  user-select: none;

  @media screen and (max-width: 767px) {
    display: none;
  }

  &:hover {
    box-shadow: 2px 0px 20px 0px rgba(0, 0, 0, 0.25);
  }

  .mapboxgl-ctrl {
    border-radius: 6px;
    box-shadow: none;
  }

  && button {
    width: 35px;
    height: 35px;
    background-size: 100% 100%;
    transition: background-color 0.4s;
  }
`;

export const ZoomControls = () => {
  const { __ } = useTranslation();

  return (
    // Note: the id property is being used by Cordova app
    <Wrapper id="zoom-controls">
      <NavigationControl
        showCompass={false}
        zoomInLabel={__('tooltips.zoomIn')}
        zoomOutLabel={__('tooltips.zoomOut')}
      />
    </Wrapper>
  );
};
