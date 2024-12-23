import { ScaleLinear } from 'd3-scale';
import { memo, useMemo } from 'react';

const CIRCLE_RADIUS = 6;

function GraphHoverLine({
  x,
  y,
  fill,
  valueScale,
  showMarker,
  setTooltipPosition,
  elementReference,
}: {
  x: number;
  y: number;
  fill: string;
  valueScale: ScaleLinear<number, number, never>;
  showMarker: boolean;
  setTooltipPosition: ({ x, y }: { x: number; y: number }) => void;
  elementReference: HTMLDivElement | null;
}) {
  const [y1, y2] = useMemo(() => valueScale.range(), [valueScale]);

  if (!elementReference) {
    return null;
  }
  const { left, top } = elementReference.getBoundingClientRect();

  setTooltipPosition({
    x: left + x,
    y: top + y,
  });

  return (
    <>
      <line
        className="vertical-line"
        style={{
          display: 'block',
          pointerEvents: 'none',
          shapeRendering: 'crispEdges',
          stroke: 'lightgray',
          strokeWidth: 1,
        }}
        x1={x}
        x2={x}
        y1={y1}
        y2={y2}
      />
      {showMarker && (
        <circle
          r={CIRCLE_RADIUS}
          style={{
            display: 'block',
            pointerEvents: 'none',
            shapeRendering: 'geometricPrecision',
            stroke: 'black',
            strokeWidth: 1.5,
            fill,
          }}
          cx={x}
          cy={y}
        />
      )}
    </>
  );
}

export default memo(GraphHoverLine);
