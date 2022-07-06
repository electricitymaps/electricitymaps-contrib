import React, { useEffect } from 'react';

const GraphHoverLine = React.memo(
  ({
    layers,
    datetimes,
    timeScale,
    valueScale,
    markerUpdateHandler,
    markerHideHandler,
    selectedLayerIndex,
    selectedTimeIndex,
    svgNode,
  }) => {
    const layer = layers && layers[selectedLayerIndex];
    const fill = layer && layer.markerFill;
    const datapoint = layer && layer.datapoints && layer.datapoints[selectedTimeIndex];

    const x = datetimes && datetimes[selectedTimeIndex] && timeScale(datetimes[selectedTimeIndex]);
    const y = datapoint && Number.isFinite(datapoint[1]) && valueScale(datapoint[1]);

    const showVerticalLine = Number.isFinite(x);
    const showMarker = Number.isFinite(x) && Number.isFinite(y);

    // Marker callbacks
    useEffect(() => {
      if (showMarker) {
        if (markerUpdateHandler && svgNode) {
          markerUpdateHandler(
            {
              x: svgNode.getBoundingClientRect().left + x,
              y: svgNode.getBoundingClientRect().top + y,
            },
            datapoint.data,
            layer.key
          );
        }
      } else if (markerHideHandler) {
        markerHideHandler();
      }
    }, [markerUpdateHandler, markerHideHandler, svgNode, showMarker, x, y, datapoint, layer]);

    return (
      <React.Fragment>
        {showVerticalLine && (
          <line
            className="vertical-line"
            style={{
              display: 'block',
              pointerEvents: 'none',
              shapeRendering: 'crispEdges',
            }}
            x1={x}
            x2={x}
            y1={valueScale.range()[0]}
            y2={valueScale.range()[1]}
          />
        )}
        {showMarker && (
          <circle
            r="6"
            style={{
              display: 'block',
              pointerEvents: 'none',
              shapeRendering: 'crispEdges',
              stroke: 'black',
              strokeWidth: 1.5,
              fill: typeof fill === 'function' ? fill(datapoint) : fill,
            }}
            cx={x}
            cy={y}
          />
        )}
      </React.Fragment>
    );
  }
);

export default GraphHoverLine;
