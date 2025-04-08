import { Group } from '@visx/group';
import { CountryFlag } from 'components/Flag';
import { noop } from 'features/charts/graphUtils';
import ProductionSourceLegend from 'features/charts/ProductionSourceLegend';
import { InfoIcon, LucideIcon, TriangleAlertIcon } from 'lucide-react';
import { memo, MouseEventHandler, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';
import type { ElectricityModeType, Maybe } from 'types';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

import {
  EXCHANGE_PADDING,
  ICON_PLUS_PADDING,
  PADDING_Y,
  ROW_HEIGHT,
  TEXT_ADJUST_Y,
} from '../constants';

type BaseProps = {
  children: React.ReactNode;
  index: number;
  isMobile: boolean;
  capacity: Maybe<number> | number[];
  value: Maybe<number>;
  onMouseOver?: MouseEventHandler<SVGRectElement>;
  onMouseOut?: () => void;
  width: number;
};

const TextElement = memo(function TextElement({ text }: { text: string }) {
  return (
    <text
      className="text-xs"
      textAnchor="start"
      fill="currentColor"
      transform={`translate(${ICON_PLUS_PADDING}, ${TEXT_ADJUST_Y})`}
    >
      {text}
    </text>
  );
});

// Generic fallback icon component
const FallbackIcon = memo(function FallbackIcon({
  width,
  IconComponent,
}: {
  width: number;
  IconComponent: LucideIcon;
}) {
  return (
    <IconComponent
      className="pointer-events-none fill-white text-neutral-300 dark:fill-neutral-800 dark:text-neutral-500"
      x={width - EXCHANGE_PADDING - DEFAULT_ICON_SIZE}
      size={DEFAULT_ICON_SIZE}
    />
  );
});

const FallbackWarning = memo(function FallbackWarning({ width }: { width: number }) {
  return <FallbackIcon width={width} IconComponent={TriangleAlertIcon} />;
});

const FallbackInfo = memo(function FallbackInfo({ width }: { width: number }) {
  return <FallbackIcon width={width} IconComponent={InfoIcon} />;
});

const RowBackground = memo(function RowBackground({
  width,
  isMobile,
  onMouseOver,
  onMouseOut,
}: {
  width: number;
  isMobile: boolean;
  onMouseOver?: MouseEventHandler<SVGRectElement>;
  onMouseOut?: () => void;
}) {
  // Use memoization to avoid unnecessary re-renders
  const onClickHandler = useMemo(
    () => (isMobile ? onMouseOver : noop),
    [isMobile, onMouseOver]
  );
  const onMouseOverHandler = useMemo(
    () => (isMobile ? noop : onMouseOver),
    [isMobile, onMouseOver]
  );
  return (
    <rect
      fill="transparent"
      width={width}
      height={ROW_HEIGHT + PADDING_Y}
      /* Support only click events in mobile mode, otherwise react to mouse hovers */
      onClick={onClickHandler}
      onMouseOver={onMouseOverHandler}
      onMouseMove={onMouseOverHandler}
      onMouseOut={onMouseOut}
      onBlur={onMouseOut}
    />
  );
});

function BaseRow({
  children,
  width,
  isMobile,
  onMouseOver,
  onMouseOut,
  value,
  capacity,
  index,
}: BaseProps) {
  // Don't render if the width is not positive
  if (width <= 0) {
    return null;
  }
  // Make sure the capacity is a number
  capacity = Array.isArray(capacity)
    ? Math.abs(capacity[0]) + Math.abs(capacity[1])
    : capacity;
  return (
    <Group top={index * (ROW_HEIGHT + PADDING_Y)}>
      {/* Row background */}
      <RowBackground
        width={width}
        isMobile={isMobile}
        onMouseOver={onMouseOver}
        onMouseOut={onMouseOut}
      />

      {/* Row content */}
      {children}

      {/* Warning icon if the value is not defined but the capacity is, info if both are undefined */}
      {!Number.isFinite(value) &&
        (Number.isFinite(capacity) ? (
          <FallbackWarning width={width} />
        ) : (
          <FallbackInfo width={width} />
        ))}
    </Group>
  );
}

type ProductionProps = { productionMode: ElectricityModeType } & BaseProps;

export function ProductionSourceRow({
  children,
  index,
  isMobile,
  productionMode,
  value,
  capacity,
  onMouseOver,
  onMouseOut,
  width,
}: ProductionProps) {
  const { t } = useTranslation();
  return (
    <BaseRow
      index={index}
      isMobile={isMobile}
      value={value}
      capacity={capacity}
      onMouseOver={onMouseOver}
      onMouseOut={onMouseOut}
      width={width}
    >
      <g className="pointer-events-none">
        <TextElement text={t(productionMode)} />
        <ProductionSourceLegend electricityType={productionMode} />
      </g>

      {/* Row content */}
      {children}
    </BaseRow>
  );
}

type ExchangeProps = { zoneKey: string } & BaseProps;

export function ExchangeRow({
  children,
  index,
  isMobile,
  zoneKey,
  value,
  capacity,
  onMouseOver,
  onMouseOut,
  width,
}: ExchangeProps) {
  const { search } = useLocation();
  return (
    <BaseRow
      index={index}
      isMobile={isMobile}
      value={value}
      capacity={capacity}
      onMouseOver={onMouseOver}
      onMouseOut={onMouseOut}
      width={width}
    >
      {/* Row label */}
      <Link to={`/zone/${zoneKey}${search}`}>
        <TextElement text={zoneKey} />
        <CountryFlag zoneId={zoneKey} />
      </Link>

      {/* Row content */}
      {children}
    </BaseRow>
  );
}
