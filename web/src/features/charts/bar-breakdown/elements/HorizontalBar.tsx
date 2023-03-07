import { ScaleLinear } from 'd3-scale';
import { Maybe } from 'types';
import { LABEL_MAX_WIDTH, RECT_OPACITY, ROW_HEIGHT } from '../constants';

type Props = {
  className: string;
  fill: string;
  range: [Maybe<number>, Maybe<number>];
  scale: ScaleLinear<number, number, never>;
};

export default function HorizontalBar({ className, fill, range, scale }: Props) {
  // Don't render if the range is not valid
  if (!Array.isArray(range) || range[0] == null || range[1] == null) {
    return null;
  }

  const x1 = Math.min(range[0], range[1]);
  const x2 = Math.max(range[0], range[1]);
  const width = scale(x2) - scale(x1);

  // Don't render if the width is not positive
  if (width <= 0) {
    return null;
  }

  return (
    <rect
      className={`pointer-events-none ${className}`}
      fill={fill}
      height={ROW_HEIGHT}
      opacity={RECT_OPACITY}
      shapeRendering="crispEdges"
      x={LABEL_MAX_WIDTH + scale(x1)}
      width={width}
    />
  );
}
