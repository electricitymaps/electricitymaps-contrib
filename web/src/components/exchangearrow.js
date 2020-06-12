import React, { useMemo } from 'react';
import { useSelector } from 'react-redux';
import styled from 'styled-components';
import { noop } from 'lodash';

import {
  quantizedCo2IntensityScale,
  quantizedExchangeSpeedScale,
} from '../helpers/scales';

// TODO: Fix map scrolling when hovering over arrows when moving map to React.
// See https://github.com/tmrowco/electricitymap-contrib/issues/2309.
const ArrowImage = styled.img`
  cursor: pointer;
  overflow: hidden;
  position: absolute;
  pointer-events: all;
  image-rendering: crisp-edges;
  left: -25px;
  top: -41px;
`;

export default React.memo(({
  data,
  mouseMoveHandler,
  mouseOutHandler,
  project,
  viewportWidth,
  viewportHeight,
}) => {
  const isMobile = useSelector(state => state.application.isMobile);
  const mapZoom = useSelector(state => state.application.mapViewport.zoom);
  const colorBlindModeEnabled = useSelector(state => state.application.colorBlindModeEnabled);
  const {
    co2intensity,
    lonlat,
    netFlow,
    rotation,
  } = data;

  const imageSource = useMemo(
    () => {
      const prefix = colorBlindModeEnabled ? 'colorblind-' : '';
      const intensity = quantizedCo2IntensityScale(co2intensity);
      const speed = quantizedExchangeSpeedScale(Math.abs(netFlow));
      return resolvePath(`images/${prefix}arrow-${intensity}-animated-${speed}.gif`);
    },
    [colorBlindModeEnabled, co2intensity, netFlow],
  );

  const transform = useMemo(
    () => ({
      x: project(lonlat)[0],
      y: project(lonlat)[1],
      k: 0.04 + (mapZoom - 1.5) * 0.1,
      r: rotation + (netFlow > 0 ? 180 : 0),
    }),
    [project, lonlat, rotation, netFlow, mapZoom],
  );

  const isVisible = useMemo(
    () => {
      // Hide arrows with a very low flow...
      if (Math.abs(netFlow || 0) < 1) return false;

      // ... or the ones that would be rendered outside of viewport ...
      if (transform.x + 100 * transform.k < 0) return false;
      if (transform.y + 100 * transform.k < 0) return false;
      if (transform.x - 100 * transform.k > viewportWidth) return false;
      if (transform.y - 100 * transform.k > viewportHeight) return false;

      // ... and show all the other ones.
      return true;
    },
    [netFlow, transform],
  );

  return (
    <ArrowImage
      style={{
        display: isVisible ? '' : 'none',
        transform: `translateX(${transform.x}px) translateY(${transform.y}px) rotate(${transform.r}deg) scale(${transform.k})`,
      }}
      src={imageSource}
      width="49"
      height="81"
      /* Support only click events in mobile mode, otherwise react to mouse hovers */
      onClick={isMobile ? (e => mouseMoveHandler(data, e.clientX, e.clientY)) : noop}
      onMouseMove={!isMobile ? (e => mouseMoveHandler(data, e.clientX, e.clientY)) : noop}
      onMouseOut={mouseOutHandler}
      onBlur={mouseOutHandler}
    />
  );
});
