import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { mapMovingAtom } from 'features/map/mapAtoms';
import { useSetAtom } from 'jotai';
import { useEffect } from 'react';
import { resolvePath } from 'react-router-dom';
import { ExchangeArrowData } from 'types';

import ExchangeTooltip from './ExchangeTooltip';
import { quantizedCo2IntensityScale, quantizedExchangeSpeedScale } from './scales';

interface ExchangeArrowProps {
  data: ExchangeArrowData;
  viewportWidth: number;
  viewportHeight: number;
  map: maplibregl.Map;
  colorBlindMode: boolean;
  isMobile: boolean;
}

function ExchangeArrow({
  data,
  viewportWidth,
  viewportHeight,
  map,
  colorBlindMode,
  isMobile,
}: ExchangeArrowProps) {
  const { ci, lonlat, f, rotation, key } = data;
  if (!lonlat) {
    return null;
  }

  const absFlow = Math.abs(f ?? 0);
  // Don't render if the flow is very low ...
  if (absFlow < 1) {
    return null;
  }
  const mapZoom = map.getZoom();
  const projection = map.project(lonlat);
  const transform = {
    x: projection.x,
    y: projection.y,
    k: 0.04 + (mapZoom - 1.5) * 0.1,
    r: rotation + (f > 0 ? 180 : 0),
  };

  if (
    // or if the arrow would be very tiny
    transform.k < 0.1 ||
    // or if it would be rendered outside of viewport.
    transform.x + 100 * transform.k < 0 ||
    transform.y + 100 * transform.k < 0 ||
    transform.x - 100 * transform.k > viewportWidth ||
    transform.y - 100 * transform.k > viewportHeight
  ) {
    return null;
  }

  const setIsMoving = useSetAtom(mapMovingAtom);

  useEffect(() => {
    const cancelWheel = (event: Event) => event.preventDefault();
    const exchangeLayer = document.querySelector('#exchange-layer');
    if (!exchangeLayer) {
      return;
    }
    exchangeLayer.addEventListener('wheel', cancelWheel, {
      passive: true,
    });
    return () => exchangeLayer.removeEventListener('wheel', cancelWheel);
  }, []);

  const prefix = colorBlindMode ? 'colorblind-' : '';
  const intensity = quantizedCo2IntensityScale(ci);
  const speed = quantizedExchangeSpeedScale(absFlow);
  const imageSource = resolvePath(
    `images/arrows/${prefix}arrow-${intensity}-animated-${speed}`
  ).pathname;

  return (
    <TooltipWrapper
      tooltipClassName={`max-h-[256px] max-w-[512px] ${isMobile ? '' : 'top-[-76px]'}`}
      tooltipContent={<ExchangeTooltip exchangeData={data} isMobile={isMobile} />}
      side={isMobile ? 'top' : 'right'}
      sideOffset={10}
    >
      <picture
        id={key}
        style={{
          transform: `translateX(${transform.x}px) translateY(${transform.y}px) rotate(${transform.r}deg) scale(${transform.k})`,
          cursor: 'pointer',
          overflow: 'hidden',
          position: 'absolute',
          pointerEvents: 'all',
          imageRendering: 'crisp-edges',
          left: '-25px',
          top: '-41px',
        }}
        onWheel={() => setIsMoving(true)}
      >
        <source srcSet={`${imageSource}.webp`} type="image/webp" />
        <img src={`${imageSource}.gif`} alt="" draggable={false} />
      </picture>
    </TooltipWrapper>
  );
}

export default ExchangeArrow;
