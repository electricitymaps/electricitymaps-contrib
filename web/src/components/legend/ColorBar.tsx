import { extent } from 'd3-array';
import { ScaleLinear, scaleLinear } from 'd3-scale';
import { memo } from 'react';

export const spreadOverDomain = (
  scale: ScaleLinear<string | number, string | number, string | number>,
  count: number
) => {
  const [x1, x2] = (extent(scale.domain()) as unknown as [number, number]) ?? [0, 0];
  return [...Array.from({ length: count }).keys()].map(
    (v) => x1 + ((x2 - x1) * v) / (count - 1)
  );
};

function HorizontalColorbar({
  colorScale,
  id,
  ticksCount = 5,
}: {
  colorScale: ScaleLinear<string, string, string>;
  id: string;
  ticksCount?: number;
}) {
  const linearScale = scaleLinear().domain(
    extent(colorScale.domain()) as unknown as [number, number]
  );

  return (
    <>
      <svg className="flex h-3 w-full flex-col overflow-visible">
        <g transform={`translate(8,0)`}>
          <linearGradient id={`${id}-gradient`} x2="100%">
            {spreadOverDomain(colorScale, 10).map((value, index) => (
              <stop key={value} offset={index / 9} stopColor={colorScale(value)} />
            ))}
          </linearGradient>
          <rect
            fill={`url(#${id}-gradient)`}
            width="100%"
            height={8}
            rx={5}
            transform="translate(-10,0)"
          />
        </g>
      </svg>

      <div className="flex flex-row justify-between pr-0.5">
        {spreadOverDomain(linearScale, ticksCount).map((t) => (
          <div
            key={t}
            className="text-xs font-medium text-neutral-600 dark:text-neutral-300"
          >
            {Math.round(t)}
          </div>
        ))}
      </div>
    </>
  );
}

export default memo(HorizontalColorbar);
