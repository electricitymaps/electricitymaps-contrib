import { ScaleLinear } from 'd3-scale';
import { memo } from 'react';

const CIRCLE_RADIUS = 6;

const GraphHoverLine = memo(
  ({
    x,
    y,
    fill,
    valueScale,
    showVerticalLine,
    showMarker,
    setTooltipPosition,
    elementReference,
  }: {
    x: number;
    y: number;
    fill: string;
    valueScale: ScaleLinear<number, number, never>;
    showVerticalLine: boolean;
    showMarker: boolean;
    setTooltipPosition: ({ x, y }: { x: number; y: number }) => void;
    elementReference: HTMLDivElement | null;
  }) => {
    if (!elementReference) {
      return null;
    }
    const [y1, y2] = valueScale.range();

    setTooltipPosition({
      x: elementReference.getBoundingClientRect().left + x,
      y: elementReference.getBoundingClientRect().top + y,
    });

    return (
      <>
        {showVerticalLine && (
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
        )}
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
);

GraphHoverLine.displayName = 'GraphHoverLine';

export default GraphHoverLine;
