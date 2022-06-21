import React from 'react';
import { NavigationControl } from 'react-map-gl';
import styled from 'styled-components';

import { useTranslation } from '../helpers/translation';
import { useFeatureToggle } from '../hooks/router';

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
    top: 66px;
    ${({ isHiddenOnMobile }) =>
      isHiddenOnMobile &&
      `
      display: none;
    `}
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
  const isHistoryFeatureEnabled = useFeatureToggle('history');
  const { __ } = useTranslation();

  return (
    // Note: the id property is being used by Cordova app
    <Wrapper id="zoom-controls" isHiddenOnMobile={isHistoryFeatureEnabled}>
      <NavigationControl
        showCompass={false}
        zoomInLabel={__('tooltips.zoomIn')}
        zoomOutLabel={__('tooltips.zoomOut')}
      />
    </Wrapper>
  );
};
