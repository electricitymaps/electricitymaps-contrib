import { ArrowLeft, ArrowRight } from 'lucide-react';
import { memo } from 'react';

import { X_AXIS_HEIGHT } from '../constants';

const ARROW_OFFSET = 3;
const HALF_ARROW_OFFSET = ARROW_OFFSET / 2;
const ARROW_SIZE = X_AXIS_HEIGHT - ARROW_OFFSET;

function BarBreakdownAxisLegend({
  height,
  legendText,
}: {
  height: number;
  legendText: { left: string; right: string };
}) {
  const ARROW_Y_POSITION = height - X_AXIS_HEIGHT + HALF_ARROW_OFFSET;
  return (
    <>
      <line
        stroke="currentColor"
        strokeWidth={1}
        shapeRendering={'auto'}
        y1={height - X_AXIS_HEIGHT}
        y2={height - X_AXIS_HEIGHT + 15}
      />
      <text
        className="fill-neutral-500"
        fontSize={'0.7rem'}
        y={height - X_AXIS_HEIGHT + 12}
        x={-18.5}
        textAnchor="end"
      >
        {legendText.left}
      </text>
      <ArrowLeft
        className="text-neutral-500"
        size={ARROW_SIZE}
        x={-15 - HALF_ARROW_OFFSET}
        y={ARROW_Y_POSITION}
      />
      <ArrowRight
        className="text-neutral-500"
        size={ARROW_SIZE}
        x={2 + HALF_ARROW_OFFSET}
        y={ARROW_Y_POSITION}
      />
      <text
        className="fill-neutral-500"
        fontSize={'0.7rem'}
        y={height - X_AXIS_HEIGHT + 12}
        x={17.5}
        textAnchor="start"
      >
        {legendText.right}
      </text>
    </>
  );
}

export default memo(BarBreakdownAxisLegend);
