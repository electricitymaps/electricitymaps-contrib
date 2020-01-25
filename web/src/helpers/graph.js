const d3 = Object.assign(
  {},
  require('d3-array'),
);

export const detectHoveredDatapointIndex = (ev, datetimes, timeScale, svgRef) => {
  if (!datetimes.length) return null;
  const dx = ev.pageX
    ? (ev.pageX - svgRef.current.getBoundingClientRect().left)
    : (d3.touches(this)[0][0]);
  const datetime = timeScale.invert(dx);
  // Find data point closest to
  let i = d3.bisectLeft(datetimes, datetime);
  if (i > 0 && datetime - datetimes[i - 1] < datetimes[i] - datetime) i -= 1;
  if (i > datetimes.length - 1) i = datetimes.length - 1;
  return i;
};
