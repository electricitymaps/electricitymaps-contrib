import { ScaleLinear, scaleLinear } from 'd3-scale';
import { extent } from 'd3-array';

const spreadOverDomain = (scale: any, count: number) => {
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
  const width = 176;
  const height = 10;

  const linearScale = scaleLinear()
    .domain(extent(colorScale.domain()) as unknown as [number, number])
    .range([0, width]);

  return (
    <svg className="flex h-10 w-full flex-col  px-2">
      <g transform={`translate(8,0)`}>
        <linearGradient id={`${id}-gradient`} x2="100%">
          {spreadOverDomain(colorScale, 10).map((value, index) => (
            <stop key={value} offset={index / 9} stopColor={colorScale(value)} />
          ))}
        </linearGradient>
        <rect fill={`url(#${id}-gradient)`} width={width} height={height} />

        <rect
          className="border"
          shapeRendering="crispEdges"
          strokeWidth="1"
          fill="none"
          width={width}
          height={height}
        />
        <g
          className="x axis"
          transform={`translate(0,${height})`}
          fill="none"
          fontSize="10"
          fontFamily="sans-serif"
          textAnchor="middle"
        >
          {spreadOverDomain(linearScale, ticksCount).map((t) => (
            <g
              key={`colorbar-tick-${t}`}
              className="tick"
              transform={`translate(${linearScale(t)},0)`}
            >
              <text fill="currentColor" y="8" dy="0.81em">
                {Math.round(t)}
              </text>
            </g>
          ))}
        </g>
      </g>
    </svg>
  );
}

export default HorizontalColorbar;
