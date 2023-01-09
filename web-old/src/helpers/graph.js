import { bisectLeft } from 'd3-array';
import { touches } from 'd3-selection';

export const detectHoveredDatapointIndex = (ev, datetimes, timeScale, svgNode) => {
  if (!datetimes.length) {
    return null;
  }
  const dx = ev.pageX ? ev.pageX - svgNode.getBoundingClientRect().left : touches(this)[0][0];
  const datetime = timeScale.invert(dx);
  // Find data point closest to
  let i = bisectLeft(datetimes, datetime);
  if (i > 0 && datetime - datetimes[i - 1] < datetimes[i] - datetime) {
    i -= 1;
  }
  if (i > datetimes.length - 1) {
    i = datetimes.length - 1;
  }
  return i;
};

// If in mobile mode, put the tooltip to the top of the screen for
// readability, otherwise float it depending on the marker position.
export const getTooltipPosition = (isMobile, marker) => (isMobile ? { x: 0, y: 0 } : marker);
