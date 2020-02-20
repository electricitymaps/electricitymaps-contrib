import React from 'react';

import { detectHoveredDatapointIndex } from '../../helpers/graph';

const GraphBackground = ({
  timeScale,
  valueScale,
  datetimes,
  mouseMoveHandler,
  mouseOutHandler,
  svgRef,
}) => {
  const [x1, x2] = timeScale.range();
  const [y2, y1] = valueScale.range();
  if (x1 >= x2 || y1 >= y2) return null;

  // Mouse hover events
  let mouseOutRectTimeout;
  const handleRectMouseMove = (ev) => {
    if (mouseOutRectTimeout) {
      clearTimeout(mouseOutRectTimeout);
      mouseOutRectTimeout = undefined;
    }
    if (mouseMoveHandler) {
      mouseMoveHandler(detectHoveredDatapointIndex(ev, datetimes, timeScale, svgRef));
    }
  };
  const handleRectMouseOut = () => {
    mouseOutRectTimeout = setTimeout(() => {
      if (mouseOutHandler) {
        mouseOutHandler();
      }
    }, 50);
  };

  return (
    <rect
      x={x1}
      y={y1}
      width={x2 - x1}
      height={y2 - y1}
      style={{ cursor: 'pointer', opacity: 0 }}
      onFocus={handleRectMouseMove}
      onMouseOver={handleRectMouseMove}
      onMouseMove={handleRectMouseMove}
      onMouseOut={handleRectMouseOut}
      onBlur={handleRectMouseOut}
    />
  );
};

export default GraphBackground;
