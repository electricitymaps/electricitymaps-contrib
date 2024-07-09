import { extent } from 'd3-array';
import { ScaleLinear } from 'd3-scale';

export const spreadOverDomain = (
  scale: ScaleLinear<string | number, string | number, string | number>,
  count: number
) => {
  const [x1, x2] = (extent(scale.domain()) as unknown as [number, number]) ?? [0, 0];
  return [...Array.from({ length: count }).keys()].map(
    (v) => x1 + ((x2 - x1) * v) / (count - 1)
  );
};
