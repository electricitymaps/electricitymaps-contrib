/* eslint-disable react/jsx-handler-names */
/* eslint-disable unicorn/no-null */
/* eslint-disable react/display-name */
import { ScaleLinear, ScaleTime } from 'd3-scale';
import React from 'react';

import { detectHoveredDatapointIndex, noop } from '../graphUtils';

interface GraphBackgroundProps {
  timeScale: ScaleTime<number, number>;
  valueScale: ScaleLinear<number, number>;
  datetimes: Date[];
  mouseMoveHandler?: (timeIndex: number | null, layerIndex: number | null) => void;
  mouseOutHandler?: () => void;
  isMobile: boolean;
  svgNode: SVGSVGElement;
}

const GraphBackground: React.FC<GraphBackgroundProps> = React.memo(
  ({
    timeScale,
    valueScale,
    datetimes,
    mouseMoveHandler,
    mouseOutHandler,
    isMobile,
    svgNode,
  }) => {
    const [x1, x2] = timeScale.range();
    const [y2, y1] = valueScale.range();
    const width = x2 - x1;
    const height = y2 - y1;

    // Mouse hover events
    let mouseOutRectTimeout: string | number | NodeJS.Timeout | undefined;
    const handleRectMouseMove = (event: React.MouseEvent<SVGRectElement>) => {
      if (mouseOutRectTimeout) {
        clearTimeout(mouseOutRectTimeout);
        mouseOutRectTimeout = undefined;
      }
      const timeIndex = detectHoveredDatapointIndex(event, datetimes, timeScale, svgNode);
      if (mouseMoveHandler) {
        mouseMoveHandler(timeIndex, null);
      }
    };
    const handleRectMouseOut = () => {
      if (mouseOutHandler) {
        mouseOutHandler();
      }
    };

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
  }
);

export default GraphBackground;
