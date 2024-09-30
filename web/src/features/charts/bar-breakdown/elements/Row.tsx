import { CountryFlag } from 'components/Flag';
import { ScaleLinear } from 'd3-scale';
import ProductionSourceLegend from 'features/charts/ProductionSourceLegend';
import { MouseEventHandler } from 'react';
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

type Props = {
  children: React.ReactNode;
  index: number;
  isMobile: boolean;
  label: string;
  scale: ScaleLinear<number, number, never>;
  value: Maybe<number>;
  onMouseOver?: MouseEventHandler<SVGRectElement>;
  onMouseOut?: () => void;
  width: number;
  isExchange: boolean;
};

export default function Row({
  children,
  index,
  isMobile,
  label,
  scale,
  value,
  onMouseOver,
  onMouseOut,
  width,
  isExchange,
}: Props) {
  const { search } = useLocation();
  const { t } = useTranslation();
  // Don't render if the width is not positive
  if (width <= 0) {
    return null;
  }
  const textElement = (
    <text
      className="text-xs"
      textAnchor="start"
      fill="currentColor"
      transform={`translate(${ICON_PLUS_PADDING}, ${TEXT_ADJUST_Y})`}
    >
      {isExchange ? label : t(label)}
    </text>
  );
  const iconElement = isExchange ? (
    <CountryFlag zoneId={label} />
  ) : (
    <ProductionSourceLegend electricityType={label as ElectricityModeType} />
  );

  return (
    <g className="row" transform={`translate(0, ${index * (ROW_HEIGHT + PADDING_Y)})`}>
      {/* Row background */}
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

      {/* Row label */}
      {isExchange ? (
        <Link to={`/zone/${label}${search}`}>
          {textElement}
          {iconElement}
        </Link>
      ) : (
        <g className="pointer-events-none">
          {textElement}
          {iconElement}
        </g>
      )}

      {/* Row content */}
      {children}

      {/* Question mark if the value is not defined */}
      {!Number.isFinite(value) && (
        <text
          transform={`translate(3, ${TEXT_ADJUST_Y})`}
          className="pointer-events-none text-xs"
          fill="darkgray"
          x={LABEL_MAX_WIDTH + scale(0)}
        >
          ?
        </text>
      )}
    </g>
  );
}
