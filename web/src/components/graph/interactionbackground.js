import React from 'react';

import { detectHoveredDatapointIndex } from '../../helpers/graph';

const InteractionBackground = ({
  timeScale,
  valueScale,
  datetimes,
  mouseMoveHandler,
  mouseOutHandler,
  svgRef,
}) => {
  const [x0, x1] = timeScale.range();
  const [y1, y0] = valueScale.range();

  let mouseOutRectTimeout;
  const handleRectMouseMove = (ev) => {
    if (mouseOutRectTimeout) {
      clearTimeout(mouseOutRectTimeout);
      mouseOutRectTimeout = undefined;
    }
    if (mouseMoveHandler) {
      mouseMoveHandler(undefined, detectHoveredDatapointIndex(ev, datetimes, timeScale, svgRef));
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
      x={x0}
      y={y0}
      width={x1 - x0}
      height={y1 - y0}
      style={{ cursor: 'pointer', opacity: 0 }}
      onFocus={handleRectMouseMove}
      onMouseOver={handleRectMouseMove}
      onMouseMove={handleRectMouseMove}
      onMouseOut={handleRectMouseOut}
      onBlur={handleRectMouseOut}
    />
  );
};

export default InteractionBackground;
