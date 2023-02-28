import { ScaleLinear } from 'd3-scale';
import { MouseEventHandler } from 'react';
import { LABEL_MAX_WIDTH, PADDING_Y, ROW_HEIGHT, TEXT_ADJUST_Y } from '../constants';
import type { Maybe } from 'types';

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
}: Props) {
  // Don't render if the width is not positive
  if (width <= 0) {
    return null;
  }

  return (
    <g className="row" transform={`translate(0, ${index * (ROW_HEIGHT + PADDING_Y)})`}>
      {/* Row background */}
      <rect
        y="-1"
        fill="transparent"
        width={width}
        height={ROW_HEIGHT + PADDING_Y}
        /* Support only click events in mobile mode, otherwise react to mouse hovers */
        onClick={isMobile ? onMouseOver : () => {}}
        onMouseOver={!isMobile ? onMouseOver : () => {}}
        onMouseMove={!isMobile ? onMouseOver : () => {}}
        onMouseOut={onMouseOut}
        onBlur={onMouseOut}
      />

      {/* Row label */}
      <text
        className="pointer-events-none"
        textAnchor="end"
        fill="currentColor"
        transform={`translate(${LABEL_MAX_WIDTH - 1.5 * PADDING_Y}, ${TEXT_ADJUST_Y})`}
      >
        {label}
      </text>

      {/* Row content */}
      {children}

      {/* Question mark if the value is not defined */}
      {!Number.isFinite(value) && (
        <text
          transform={`translate(3, ${TEXT_ADJUST_Y})`}
          className="pointer-events-none"
          fill="darkgray"
          x={LABEL_MAX_WIDTH + scale(0)}
        >
          ?
        </text>
      )}
    </g>
  );
}
