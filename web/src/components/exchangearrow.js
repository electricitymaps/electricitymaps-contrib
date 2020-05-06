import React, { useMemo } from 'react';
import { useSelector } from 'react-redux';
import styled, { keyframes } from 'styled-components';
import { noop } from 'lodash';

import {
  quantizedCo2IntensityScale,
  quantizedExchangeSpeedScale,
} from '../helpers/scales';

const slidingHighlight = keyframes`
  0% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0) 0%, rgba(0,0,0,0) 0%); }
  10% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.2) 5%, rgba(0,0,0,0) 10%); }
  15% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.3) 15%, rgba(0,0,0,0) 30%); }
  20% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.4) 20%, rgba(0,0,0,0) 40%); }
  25% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.4) 25%, rgba(0,0,0,0) 50%); }
  30% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.5) 30%, rgba(0,0,0,0) 60%); }
  35% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 5%, rgba(0,0,0,0.5) 35%, rgba(0,0,0,0) 65%); }
  40% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 10%, rgba(0,0,0,0.6) 40%, rgba(0,0,0,0) 70%); }
  45% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 15%, rgba(0,0,0,0.6) 45%, rgba(0,0,0,0) 75%); }
  50% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 20%, rgba(0,0,0,0.7) 50%, rgba(0,0,0,0) 80%); }
  55% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 25%, rgba(0,0,0,0.6) 55%, rgba(0,0,0,0) 85%); }
  60% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 30%, rgba(0,0,0,0.6) 60%, rgba(0,0,0,0) 90%); }
  65% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 35%, rgba(0,0,0,0.5) 65%, rgba(0,0,0,0) 95%); }
  70% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 40%, rgba(0,0,0,0.5) 70%, rgba(0,0,0,0) 100%); }
  75% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 50%, rgba(0,0,0,0.4) 75%, rgba(0,0,0,0) 100%); }
  80% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 60%, rgba(0,0,0,0.4) 80%, rgba(0,0,0,0) 100%); }
  85% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 70%, rgba(0,0,0,0.3) 85%, rgba(0,0,0,0) 100%); }
  90% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 90%, rgba(0,0,0,0.2) 95%, rgba(0,0,0,0) 100%); }
  100% { mask-image: linear-gradient(to bottom, rgba(0,0,0,0) 100%, rgba(0,0,0,0) 100%, rgba(0,0,0,0) 100%); }
`;

const ArrowImage = styled.img`
  overflow: hidden;
  position: absolute;
  image-rendering: crisp-edges;
  left: -25px;
  top: -41px;
  width: 50px;
  height: 82px;
`;

const AnimatedHighlight = styled(ArrowImage)`
  animation: ${slidingHighlight} ${props => props.speed} infinite;
`;

export default React.memo(({
  co2intensity,
  lonlat,
  mouseMoveHandler,
  mouseOutHandler,
  netFlow,
  project,
  rotation,
  tooltipData,
  viewportWidth,
  viewportHeight,
}) => {
  const isMobile = useSelector(state => state.application.isMobile);
  const mapZoom = useSelector(state => state.application.mapViewport.zoom);
  const colorBlindModeEnabled = useSelector(state => state.application.colorBlindModeEnabled);

  const absFlow = Math.abs(netFlow || 0);
  const prefix = colorBlindModeEnabled ? 'colorblind-' : '';
  const intensity = quantizedCo2IntensityScale(co2intensity);
  const speed = quantizedExchangeSpeedScale(absFlow);

  const transform = useMemo(
    () => ({
      x: project(lonlat)[0],
      y: project(lonlat)[1],
      k: 0.04 + (mapZoom - 1.5) * 0.1,
      r: rotation + (netFlow > 0 ? 180 : 0),
    }),
    [project, lonlat, rotation, netFlow, mapZoom],
  );

  // Don't render if the flow is very low ...
  if (absFlow < 1) return null;

  // ... or if the arrow would be very tiny ...
  if (transform.k < 0.1) return null;

  // ... or if it would be rendered outside of viewport.
  if (transform.x + 100 * transform.k < 0) return null;
  if (transform.y + 100 * transform.k < 0) return null;
  if (transform.x - 100 * transform.k > viewportWidth) return null;
  if (transform.y - 100 * transform.k > viewportHeight) return null;

  return (
    <div
      className="arrow"
      style={{
        transform: `translateX(${transform.x}px) translateY(${transform.y}px) rotate(${transform.r}deg) scale(${transform.k})`,
        position: 'absolute',
      }}
    >
      <ArrowImage
        style={{ cursor: 'pointer', pointerEvents: 'all' }}
        src={resolvePath(`images/${prefix}arrow-${intensity}.png`)}
        /* Support only click events in mobile mode, otherwise react to mouse hovers */
        onClick={isMobile ? (e => mouseMoveHandler(tooltipData, e.clientX, e.clientY)) : noop}
        onMouseMove={!isMobile ? (e => mouseMoveHandler(tooltipData, e.clientX, e.clientY)) : noop}
        onMouseOut={mouseOutHandler}
        onBlur={mouseOutHandler}
      />
      <AnimatedHighlight src={resolvePath('images/arrow-highlight.png')} speed={speed} />
    </div>
  );
});
