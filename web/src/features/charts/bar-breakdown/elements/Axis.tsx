import { ScaleLinear } from 'd3-scale';

import { LABEL_MAX_WIDTH, SCALE_TICKS, X_AXIS_HEIGHT } from '../constants';
import BarBreakdownAxisLegend from './BarBreakdownAxisLegend';

type Props = {
  height: number;
  scale: ScaleLinear<number, number, never>;
  formatTick: (tick: number) => string | number;
  axisLegendText?: { left: string; right: string };
};

export default function Axis({ formatTick, height, scale, axisLegendText }: Props) {
  const axisTicks = scale.ticks(SCALE_TICKS);

  return (
    <g
      className="text-gray-500/30"
      fill="none"
      fontSize="10"
      fontFamily="sans-serif"
      textAnchor="middle"
      transform={`translate(${scale.range()[0] + LABEL_MAX_WIDTH}, ${X_AXIS_HEIGHT})`}
    >
      <path
        stroke="currentColor"
        fill="none"
        shapeRendering="auto"
        d={`M${scale.range()[0] + 0.5},0.5H${scale.range()[1] + 0.5}`}
      />
      {axisTicks.map((t) => (
        <g key={t} className="tick" opacity="1" transform={`translate(${scale(t)}, 0)`}>
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
            {formatTick(t)}
          </text>
          {axisLegendText && t == 0 && (
            <BarBreakdownAxisLegend height={height} legendText={axisLegendText} />
          )}
        </g>
      ))}
    </g>
  );
}
