import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { mapMovingAtom } from 'features/map/mapAtoms';
import { useHeaderHeight } from 'hooks/headerHeight';
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
  const { co2intensity, lonlat, netFlow, rotation, key } = data;

  const setIsMoving = useSetAtom(mapMovingAtom);
  const headerHeight = useHeaderHeight();

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

  const absFlow = Math.abs(netFlow ?? 0);

  // Don't render if there is no position or if flow is very low ...
  if (!lonlat || absFlow < 1) {
    return null;
  }

  const mapZoom = map.getZoom();
  const projection = map.project(lonlat);
  const transform = {
    x: projection.x,
    y: projection.y,
    k: 0.04 + (mapZoom - 1.5) * 0.1,
    r: rotation + (netFlow > 0 ? 180 : 0),
  };

  // Setting the top position from the arrow tooltip preventing overflowing to top.
  let tooltipClassName =
    'max-h-[256px] max-w-[512px] md:flex rounded-2xl border-neutral-200 bg-white dark:bg-gray-900 dark:border-gray-700 dark:border';
  if (!isMobile) {
    tooltipClassName += transform.y - 76 < headerHeight ? ' top-[76px]' : ' top-[-76px]';
  }

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

  const prefix = colorBlindMode ? 'colorblind-' : '';
  const intensity = quantizedCo2IntensityScale(co2intensity);
  const speed = quantizedExchangeSpeedScale(absFlow);
  const imageSource = resolvePath(
    `images/arrows/${prefix}arrow-${intensity}-animated-${speed}`
  ).pathname;

  return (
    <TooltipWrapper
      tooltipClassName={tooltipClassName}
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
          pointerEvents: isMobile ? 'all' : 'none',
          imageRendering: 'crisp-edges',
          left: '-25px',
          top: '-41px',
        }}
        onWheel={() => setIsMoving(true)}
        data-testid={`exchange-arrow-${key}`}
      >
        <source srcSet={`${imageSource}.webp`} type="image/webp" />
        <img src={`${imageSource}.gif`} alt="" draggable={false} />
      </picture>
    </TooltipWrapper>
  );
}

export default ExchangeArrow;
