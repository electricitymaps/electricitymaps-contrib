/* eslint-disable react/display-name */
import React, { useEffect } from 'react';

const CIRCLE_RADIUS = 6;

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
  }: any) => {
    const layer = layers && layers[selectedLayerIndex];
    const fill = layer && layer.markerFill;
    const datapoint = layer && layer.datapoints && layer.datapoints[selectedTimeIndex];
    const interval =
      datetimes && datetimes.length > 1
        ? timeScale(datetimes[1]) - timeScale(datetimes[0])
        : undefined;
    let x =
      datetimes &&
      datetimes[selectedTimeIndex] &&
      timeScale(datetimes[selectedTimeIndex]);
    if (interval) {
      x += 0.5 * interval;
    }
    let y = datapoint && Number.isFinite(datapoint[1]) && valueScale(datapoint[1]);

    if (datapoint && datapoint[0] < 0) {
      // For negative values, we push the circle below the x-axis
      y -= datapoint[0] + CIRCLE_RADIUS;
    }

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
    }, [
      markerUpdateHandler,
      markerHideHandler,
      svgNode,
      showMarker,
      x,
      y,
      datapoint,
      layer,
    ]);

    return (
      <React.Fragment>
        {showVerticalLine && (
          <line
            id="liners"
            className="vertical-line"
            style={{
              display: 'block',
              pointerEvents: 'none',
              shapeRendering: 'crispEdges',
              stroke: 'lightgray',
              strokeWidth: 1,
            }}
            x1={x}
            x2={x}
            y1={valueScale.range()[0]}
            y2={valueScale.range()[1]}
          />
        )}
        {showMarker && (
          <circle
            r={CIRCLE_RADIUS}
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
