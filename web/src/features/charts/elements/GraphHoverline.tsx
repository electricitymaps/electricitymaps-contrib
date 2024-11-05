/* eslint-disable react/display-name */
import React, { useEffect } from 'react';

const CIRCLE_RADIUS = 6;

const GraphHoverLine = React.memo(
  ({
    layers,
    datetimes,
    endTime,
    timeScale,
    valueScale,
    markerUpdateHandler,
    markerHideHandler,
    hoverLayerIndex,
    selectedTimeIndex,
    svgNode,
  }: any) => {
    const layer = layers?.[hoverLayerIndex];
    const fill = layer?.markerFill;
    const datapoint = layer?.datapoints?.[selectedTimeIndex];
    const nextDateTime = datetimes
      ? datetimes[selectedTimeIndex + 1] ?? endTime
      : undefined;
    const interval =
      nextDateTime && datetimes[selectedTimeIndex]
        ? timeScale(nextDateTime) - timeScale(datetimes[selectedTimeIndex])
        : undefined;
    let x = datetimes?.[selectedTimeIndex] && timeScale(datetimes[selectedTimeIndex]);
    if (interval) {
      x += 0.5 * interval;
    }

    // For negative values we use the first value in the array
    // For positive values we use the second value in the array
    const yIndex = datapoint?.at(0) < 0 ? 0 : 1;
    const y = Number.isFinite(datapoint?.at(yIndex)) && valueScale(datapoint?.at(yIndex));

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
              shapeRendering: 'geometricPrecision',
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
