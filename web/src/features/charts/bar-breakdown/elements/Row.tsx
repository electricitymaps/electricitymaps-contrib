import { Group } from '@visx/group';
import { CountryFlag } from 'components/Flag';
import { ScaleLinear } from 'd3-scale';
import ProductionSourceLegend from 'features/charts/ProductionSourceLegend';
import { memo, MouseEventHandler } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';
import type { ElectricityModeType, Maybe } from 'types';

import {
  ICON_PLUS_PADDING,
  LABEL_MAX_WIDTH,
  PADDING_Y,
  ROW_HEIGHT,
  TEXT_ADJUST_Y,
} from '../constants';

type BaseProps = {
  children: React.ReactNode;
  index: number;
  isMobile: boolean;
  scale: ScaleLinear<number, number, never>;
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

const FallbackQuestionMark = memo(function FallbackQuestionMark({
  scale,
}: {
  scale: ScaleLinear<number, number, never>;
}) {
  return (
    <text
      transform={`translate(3, ${TEXT_ADJUST_Y})`}
      className="pointer-events-none text-xs"
      fill="darkgray"
      x={LABEL_MAX_WIDTH + scale(0)}
    >
      ?
    </text>
  );
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
  return (
    <rect
      fill="transparent"
      width={width}
      height={ROW_HEIGHT + PADDING_Y}
      /* Support only click events in mobile mode, otherwise react to mouse hovers */
      onClick={isMobile ? onMouseOver : () => {}}
      onMouseOver={isMobile ? () => {} : onMouseOver}
      onMouseMove={isMobile ? () => {} : onMouseOver}
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
  scale,
  index,
}: BaseProps) {
  // Don't render if the width is not positive
  if (width <= 0) {
    return null;
  }
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

      {/* Question mark if the value is not defined */}
      {!Number.isFinite(value) && <FallbackQuestionMark scale={scale} />}
    </Group>
  );
}

type ProductionProps = { productionMode: ElectricityModeType } & BaseProps;

export function ProductionSourceRow({
  children,
  index,
  isMobile,
  productionMode,
  scale,
  value,
  onMouseOver,
  onMouseOut,
  width,
}: ProductionProps) {
  const { t } = useTranslation();
  return (
    <BaseRow
      index={index}
      isMobile={isMobile}
      scale={scale}
      value={value}
      onMouseOver={onMouseOver}
      onMouseOut={onMouseOut}
      width={width}
    >
      <g className="pointer-events-none">
        <TextElement text={t(($) => $[productionMode])} />
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
  scale,
  value,
  onMouseOver,
  onMouseOut,
  width,
}: ExchangeProps) {
  const { search } = useLocation();
  return (
    <BaseRow
      index={index}
      isMobile={isMobile}
      scale={scale}
      value={value}
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
