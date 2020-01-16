import React from 'react';

const HoverLine = ({
  fill,
  data,
  datetimes,
  timeScale,
  valueScale,
  selectedTimeIndex,
}) => (
  <React.Fragment>
    {Number.isInteger(selectedTimeIndex) && (
      <line
        className="vertical-line"
        style={{
          display: 'block',
          pointerEvents: 'none',
          shapeRendering: 'crispEdges',
        }}
        x1={timeScale(datetimes[selectedTimeIndex])}
        x2={timeScale(datetimes[selectedTimeIndex])}
        y1={valueScale.range()[0]}
        y2={valueScale.range()[1]}
      />
    )}
    {Number.isInteger(selectedTimeIndex) && data && (
      <circle
        r="6"
        style={{
          display: 'block',
          pointerEvents: 'none',
          shapeRendering: 'crispEdges',
          stroke: 'black',
          strokeWidth: 1.5,
          fill,
        }}
        cx={timeScale(datetimes[selectedTimeIndex])}
        cy={valueScale(data[selectedTimeIndex][1])}
      />
    )}
  </React.Fragment>
);

export default HoverLine;
