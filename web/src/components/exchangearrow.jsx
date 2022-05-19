import React, { useMemo } from 'react';
import { useSelector } from 'react-redux';
import styled from 'styled-components';
import { noop } from '../helpers/noop';

import { quantizedCo2IntensityScale, quantizedExchangeSpeedScale } from '../helpers/scales';

const ArrowPicture = styled.picture`
  cursor: pointer;
  overflow: hidden;
  position: absolute;
  pointer-events: all;
  image-rendering: crisp-edges;
  left: -25px;
  top: -41px;
`;

export default React.memo(({ data, mouseMoveHandler, mouseOutHandler, project, viewportWidth, viewportHeight }) => {
  const isMobile = useSelector((state) => state.application.isMobile);
  const mapZoom = useSelector((state) => state.application.mapViewport.zoom);
  const colorBlindModeEnabled = useSelector((state) => state.application.colorBlindModeEnabled);
  const absFlow = Math.abs(data.netFlow || 0);
  const { co2intensity, lonlat, netFlow, rotation } = data;

  const imageSource = useMemo(() => {
    const prefix = colorBlindModeEnabled ? 'colorblind-' : '';
    const intensity = quantizedCo2IntensityScale(co2intensity);
    const speed = quantizedExchangeSpeedScale(Math.abs(netFlow));
    return resolvePath(`images/arrows/${prefix}arrow-${intensity}-animated-${speed}`);
  }, [colorBlindModeEnabled, co2intensity, netFlow]);

  const transform = useMemo(
    () => ({
      x: project(lonlat)[0],
      y: project(lonlat)[1],
      k: 0.04 + (mapZoom - 1.5) * 0.1,
      r: rotation + (netFlow > 0 ? 180 : 0),
    }),
    [project, lonlat, rotation, netFlow, mapZoom]
  );

  // Don't render if the flow is very low ...
  if (absFlow < 1) {
    return null;
  }

  // ... or if the arrow would be very tiny ...
  if (transform.k < 0.1) {
    return null;
  }

  // ... or if it would be rendered outside of viewport.
  if (transform.x + 100 * transform.k < 0) {
    return null;
  }
  if (transform.y + 100 * transform.k < 0) {
    return null;
  }
  if (transform.x - 100 * transform.k > viewportWidth) {
    return null;
  }
  if (transform.y - 100 * transform.k > viewportHeight) {
    return null;
  }

  return (
    <ArrowPicture
      style={{
        transform: `translateX(${transform.x}px) translateY(${transform.y}px) rotate(${transform.r}deg) scale(${transform.k})`,
      }}
      width="49"
      height="81"
      /* Support only click events in mobile mode, otherwise react to mouse hovers */
      onClick={isMobile ? (e) => mouseMoveHandler(data, e.clientX, e.clientY) : noop}
      onMouseMove={!isMobile ? (e) => mouseMoveHandler(data, e.clientX, e.clientY) : noop}
      onMouseOut={mouseOutHandler}
      onBlur={mouseOutHandler}
    >
      <source srcSet={`${imageSource}.webp`} type="image/webp" />
      <img src={`${imageSource}.gif`} alt="" />
    </ArrowPicture>
  );
});
