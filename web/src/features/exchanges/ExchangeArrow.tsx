/* eslint-disable unicorn/no-null */
import TooltipWrapper from 'components/TooltipWrapper';
import { useMemo } from 'react';
import { MapboxMap } from 'react-map-gl';
import { resolvePath } from 'react-router-dom';
import { ExchangeArrowData } from 'types';
import { quantizedCo2IntensityScale, quantizedExchangeSpeedScale } from 'utils/scales';
import ExchangeTooltip from './ExchangeTooltip';

interface ExchangeArrowProps {
  data: ExchangeArrowData;
  viewportWidth: number;
  viewportHeight: number;
  map: MapboxMap;
}

function ExchangeArrow({ data, viewportWidth, viewportHeight, map }: ExchangeArrowProps) {
  const mapZoom = map.getZoom();
  const colorBlindModeEnabled = false; // TODO: FIX
  const absFlow = Math.abs(data.netFlow ?? 0);
  const { co2intensity, lonlat, netFlow, rotation, key } = data;

  if (!lonlat) {
    return null;
  }

  const imageSource = useMemo(() => {
    const prefix = colorBlindModeEnabled ? 'colorblind-' : '';
    const intensity = quantizedCo2IntensityScale(co2intensity);
    const speed = quantizedExchangeSpeedScale(Math.abs(netFlow));
    return resolvePath(`arrows/${prefix}arrow-${intensity}-animated-${speed}`).pathname;
  }, [colorBlindModeEnabled, co2intensity, netFlow]);

  const projection = map.project(lonlat);

  const transform = {
    x: projection.x,
    y: projection.y,
    k: 0.04 + (mapZoom - 1.5) * 0.1,
    r: rotation + (netFlow > 0 ? 180 : 0),
  };

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
    <TooltipWrapper
      tooltipClassName="relative flex max-h-[256px] max-w-[512px] top-[-76px] rounded border bg-white p-1 px-1  text-sm drop-shadow-sm dark:border-0 dark:bg-gray-900"
      tooltipContent={<ExchangeTooltip exchangeData={data} />}
      side="right"
      sideOffset={10}
    >
      <div
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
      >
        <source srcSet={`${imageSource}.webp`} type="image/webp" />
        <img src={`${imageSource}.gif`} alt="" draggable={false} />
      </div>
    </TooltipWrapper>
  );
}

export default ExchangeArrow;
