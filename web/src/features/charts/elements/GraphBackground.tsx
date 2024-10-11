import { ScaleLinear, ScaleTime } from 'd3-scale';
import React, { useCallback, useMemo } from 'react';

import { detectHoveredDatapointIndex, noop } from '../graphUtils';

interface GraphBackgroundProps {
  timeScale: ScaleTime<number, number>;
  valueScale: ScaleLinear<number, number>;
  datetimes: Date[];
  mouseMoveHandler?: (timeIndex: number | null, layerIndex: number | null) => void;
  mouseOutHandler?: () => void;
  isMobile: boolean;
  svgNode: SVGSVGElement;
  displayName?: string;
}

const GraphBackground = React.memo(function GraphBackground({
  timeScale,
  valueScale,
  datetimes,
  mouseMoveHandler,
  mouseOutHandler,
  isMobile,
  svgNode,
}: GraphBackgroundProps) {
  const [x1, x2] = useMemo(() => timeScale.range(), [timeScale]);
  const [y2, y1] = useMemo(() => valueScale.range(), [valueScale]);
  const width = x2 - x1;
  const height = y2 - y1;
  const handleRectMouseMove = useCallback(
    (event: React.MouseEvent<SVGRectElement>) => {
      const timeIndex = detectHoveredDatapointIndex(event, datetimes, timeScale, svgNode);
      if (mouseMoveHandler) {
        mouseMoveHandler(timeIndex, null);
      }
    },
    [datetimes, timeScale, svgNode, mouseMoveHandler]
  );

  const handleRectMouseOut = useCallback(() => {
    mouseOutHandler?.();
  }, [mouseOutHandler]);

  // Don't render if the dimensions are not positive
  if (width <= 0 || height <= 0) {
    return null;
  }

  return (
    <rect
      x={x1}
      y={y1}
      width={width}
      height={height}
      style={{ cursor: 'pointer', opacity: 0 }}
      onMouseOver={isMobile ? noop : handleRectMouseMove}
      onMouseMove={isMobile ? noop : handleRectMouseMove}
      onMouseOut={handleRectMouseOut}
      onBlur={handleRectMouseOut}
    />
  );
});

export default GraphBackground;
