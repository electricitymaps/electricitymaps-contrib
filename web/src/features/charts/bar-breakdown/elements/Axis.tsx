import { Group } from '@visx/group';
import { ScaleLinear } from 'd3-scale';
import { memo } from 'react';

import { LABEL_MAX_WIDTH, SCALE_TICKS, X_AXIS_HEIGHT } from '../constants';
import BarBreakdownAxisLegend from './BarBreakdownAxisLegend';

export type FormatTick = (tick: number) => string | number;

type Props = {
  height: number;
  scale: ScaleLinear<number, number, never>;
  formatTick: FormatTick;
  axisLegendTextLeft?: string;
  axisLegendTextRight?: string;
};

function Axis({
  formatTick,
  height,
  scale,
  axisLegendTextLeft,
  axisLegendTextRight,
}: Props) {
  const axisTicks = scale.ticks(SCALE_TICKS);
  const [rangeStart, rangeEnd] = scale.range();
  return (
    <Group
      className="text-gray-500/30"
      fill="none"
      fontSize="10"
      fontFamily="sans-serif"
      textAnchor="middle"
      left={rangeStart + LABEL_MAX_WIDTH}
      top={X_AXIS_HEIGHT}
    >
      <path
        stroke="currentColor"
        fill="none"
        shapeRendering="auto"
        d={`M${rangeStart + 0.5},0.5H${rangeEnd + 0.5}`}
      />
      {axisTicks.map((tick) => (
        <Group key={tick} className="tick" opacity="1" left={scale(tick)}>
          <line
            stroke="currentColor"
            strokeWidth={1}
            shapeRendering={'auto'}
            y2={height - X_AXIS_HEIGHT}
          />
          <text
            fill="gray"
            fontSize={axisTicks.length > SCALE_TICKS ? '0.5rem' : '0.6rem'}
            y="-3"
            dy="0"
          >
            {formatTick(tick)}
          </text>
          {axisLegendTextLeft && axisLegendTextRight && tick == 0 && (
            <BarBreakdownAxisLegend
              height={height}
              legendTextLeft={axisLegendTextLeft}
              legendTextRight={axisLegendTextRight}
            />
          )}
        </Group>
      ))}
    </Group>
  );
}

export default memo(Axis);
