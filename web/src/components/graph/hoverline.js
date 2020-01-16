import React from 'react';

const HoverLine = ({
  layers,
  graphData,
  timeScale,
  valueScale,
  selectedTimeIndex,
  selectedLayerIndex,
  fillSelector,
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
        x1={timeScale(graphData[selectedTimeIndex].datetime)}
        x2={timeScale(graphData[selectedTimeIndex].datetime)}
        y1={valueScale.range()[0]}
        y2={valueScale.range()[1]}
      />
    )}
    {Number.isInteger(selectedTimeIndex) && Number.isInteger(selectedLayerIndex) && (
      <circle
        r="6"
        style={{
          display: 'block',
          pointerEvents: 'none',
          shapeRendering: 'crispEdges',
          stroke: 'black',
          strokeWidth: 1.5,
          fill: fillSelector(selectedLayerIndex),
        }}
        cx={timeScale(graphData[selectedTimeIndex].datetime)}
        cy={valueScale(layers[selectedLayerIndex].data[selectedTimeIndex][1])}
      />
    )}
  </React.Fragment>
);

export default HoverLine;
