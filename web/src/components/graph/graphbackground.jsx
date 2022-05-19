import React from 'react';
import { noop } from '../../helpers/noop';

import { detectHoveredDatapointIndex } from '../../helpers/graph';

const GraphBackground = React.memo(
  ({ timeScale, valueScale, datetimes, mouseMoveHandler, mouseOutHandler, isMobile, svgNode }) => {
    const [x1, x2] = timeScale.range();
    const [y2, y1] = valueScale.range();
    const width = x2 - x1;
    const height = y2 - y1;

    // Mouse hover events
    let mouseOutRectTimeout;
    const handleRectMouseMove = (ev) => {
      if (mouseOutRectTimeout) {
        clearTimeout(mouseOutRectTimeout);
        mouseOutRectTimeout = undefined;
      }
      const timeIndex = detectHoveredDatapointIndex(ev, datetimes, timeScale, svgNode);
      if (mouseMoveHandler) {
        mouseMoveHandler(timeIndex);
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
        /* Support only click events in mobile mode, otherwise react to mouse hovers */
        onClick={isMobile ? handleRectMouseMove : noop}
        onFocus={!isMobile ? handleRectMouseMove : noop}
        onMouseOver={!isMobile ? handleRectMouseMove : noop}
        onMouseMove={!isMobile ? handleRectMouseMove : noop}
        onMouseOut={handleRectMouseOut}
        onBlur={handleRectMouseOut}
      />
    );
  }
);

export default GraphBackground;
