import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { mapMovingAtom } from 'features/map/mapAtoms';
import { useSetAtom } from 'jotai';
import { useCallback, useEffect } from 'react';
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

  const handlePointerDown = useCallback(
    (event: React.PointerEvent) => {
      event.preventDefault();
      event.stopPropagation();

      const mapCanvas = map.getCanvas();

      const mouseDown = new MouseEvent('mousedown', {
        clientX: event.clientX,
        clientY: event.clientY,
        bubbles: true,
        cancelable: true,
        view: window,
        button: 0,
        buttons: 1,
      });
      mapCanvas.dispatchEvent(mouseDown);

      const handleMove = (moveEvent: PointerEvent) => {
        moveEvent.preventDefault();
        moveEvent.stopPropagation();

        const mouseMove = new MouseEvent('mousemove', {
          clientX: moveEvent.clientX,
          clientY: moveEvent.clientY,
          bubbles: true,
          cancelable: true,
          view: window,
          button: 0,
          buttons: 1,
        });
        mapCanvas.dispatchEvent(mouseMove);
      };

      const handleUp = (upEvent: PointerEvent) => {
        upEvent.preventDefault();
        upEvent.stopPropagation();

        const mouseUp = new MouseEvent('mouseup', {
          clientX: upEvent.clientX,
          clientY: upEvent.clientY,
          bubbles: true,
          cancelable: true,
          view: window,
          button: 0,
          buttons: 0,
        });
        mapCanvas.dispatchEvent(mouseUp);

        document.removeEventListener('pointermove', handleMove);
        document.removeEventListener('pointerup', handleUp);
      };

      document.addEventListener('pointermove', handleMove);
      document.addEventListener('pointerup', handleUp);
    },
    [map]
  );

  const absFlow = Math.abs(netFlow ?? 0);

  if (!lonlat || absFlow < 1) {
    return null;
  }

  const mapZoom = map.getZoom();
  const { x, y } = map.project(lonlat);
  const baseZoom = 0.04 + (mapZoom - 1.5) * 0.1;
  const directionalRotation = rotation + (netFlow > 0 ? 180 : 0);
  const scaledZoom = 100 * baseZoom;

  // Setting the top position from the arrow tooltip preventing overflowing to top.
  let tooltipClassName = 'max-h-[256px] max-w-[512px] md:flex';
  if (!isMobile) {
    tooltipClassName += y < 140 ? ' top-[76px]' : ' top-[-76px]';
  }

  if (
    // or if the arrow would be very tiny
    baseZoom < 0.1 ||
    // or if it would be rendered outside of viewport.
    x + scaledZoom < 0 ||
    y + scaledZoom < 0 ||
    x - scaledZoom > viewportWidth ||
    y - scaledZoom > viewportHeight
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
      tooltipContent={
        <ExchangeTooltip
          exchangeData={data}
          isMobile={isMobile}
          className={tooltipClassName}
        />
      }
      side={isMobile ? 'top' : 'right'}
      sideOffset={isMobile ? 10 : 0}
      tooltipId={`exchange-${key}`}
    >
      <picture
        style={{
          transform: `translateX(${x}px) translateY(${y}px) rotate(${directionalRotation}deg) scale(${baseZoom})`,
          cursor: 'grab',
          overflow: 'hidden',
          position: 'absolute',
          imageRendering: 'crisp-edges',
          left: '-25px',
          top: '-41px',
          pointerEvents: 'all',
          touchAction: 'none',
        }}
        onPointerDown={handlePointerDown}
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
