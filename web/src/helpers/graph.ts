import { bisectLeft } from 'd3-array';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'd3-s... Remove this comment to see the full error message
import { touches } from 'd3-selection';

export const detectHoveredDatapointIndex = (ev: any, datetimes: any, timeScale: any, svgNode: any) => {
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
export const getTooltipPosition = (isMobile: any, marker: any) => (isMobile ? { x: 0, y: 0 } : marker);
