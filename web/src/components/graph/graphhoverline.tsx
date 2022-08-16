import React, { useEffect } from 'react';

interface GraphHoverLineProps {
  layers: any;
  datetimes: any;
  timeScale: any;
  valueScale: any;
  markerUpdateHandler: any;
  markerHideHandler: any;
  selectedLayerIndex: any;
  selectedTimeIndex: any;
  svgNode: any;
}

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
  }: GraphHoverLineProps) => {
    const layer = layers && layers[selectedLayerIndex];
    const fill = layer && layer.markerFill;
    const datapoint = layer && layer.datapoints && layer.datapoints[selectedTimeIndex];
    const interval = datetimes && datetimes.length > 1 ? timeScale(datetimes[1]) - timeScale(datetimes[0]) : undefined;
    let x = datetimes && datetimes[selectedTimeIndex] && timeScale(datetimes[selectedTimeIndex]);
    if (interval) {
      x += 0.5 * interval;
    }
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
