import React from 'react';

const HoverLine = ({
  graphData,
  layerData,
  timeScale,
  valueScale,
  selectedIndex,
  fill,
}) => (
  <React.Fragment>
    {Number.isInteger(selectedIndex) && (
      <line
        className="vertical-line"
        style={{
          display: 'block',
          pointerEvents: 'none',
          shapeRendering: 'crispEdges',
        }}
        x1={timeScale(graphData[selectedIndex].datetime)}
        x2={timeScale(graphData[selectedIndex].datetime)}
        y1={valueScale.range()[0]}
        y2={valueScale.range()[1]}
      />
    )}
    {Number.isInteger(selectedIndex) && layerData && (
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
        cx={timeScale(graphData[selectedIndex].datetime)}
        cy={valueScale(layerData[selectedIndex][1])}
      />
    )}
  </React.Fragment>
);

export default HoverLine;
