import React from 'react';
import { noop } from 'lodash';

import { detectHoveredDatapointIndex } from '../../helpers/graph';

const GraphBackground = React.memo(({
  layers,
  timeScale,
  valueScale,
  datetimes,
  mouseMoveHandler,
  mouseOutHandler,
  isMobile,
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
    const timeIndex = detectHoveredDatapointIndex(ev, datetimes, timeScale, svgRef);
    if (mouseMoveHandler) {
      mouseMoveHandler(timeIndex, layers, ev, svgRef);
    }
  };
  const handleRectMouseOut = () => {
    if (mouseOutHandler) {
      mouseOutHandler();
    }
  };

  return (
    <rect
      x={x1}
      y={y1}
      width={x2 - x1}
      height={y2 - y1}
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
});

export default GraphBackground;
