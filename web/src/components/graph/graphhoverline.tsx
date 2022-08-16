import React, { useEffect } from 'react';

const GraphHoverLine = React.memo(
  ({
    // @ts-expect-error TS(2339): Property 'layers' does not exist on type '{}'.
    layers,
    // @ts-expect-error TS(2339): Property 'datetimes' does not exist on type '{}'.
    datetimes,
    // @ts-expect-error TS(2339): Property 'timeScale' does not exist on type '{}'.
    timeScale,
    // @ts-expect-error TS(2339): Property 'valueScale' does not exist on type '{}'.
    valueScale,
    // @ts-expect-error TS(2339): Property 'markerUpdateHandler' does not exist on t... Remove this comment to see the full error message
    markerUpdateHandler,
    // @ts-expect-error TS(2339): Property 'markerHideHandler' does not exist on typ... Remove this comment to see the full error message
    markerHideHandler,
    // @ts-expect-error TS(2339): Property 'selectedLayerIndex' does not exist on ty... Remove this comment to see the full error message
    selectedLayerIndex,
    // @ts-expect-error TS(2339): Property 'selectedTimeIndex' does not exist on typ... Remove this comment to see the full error message
    selectedTimeIndex,
    // @ts-expect-error TS(2339): Property 'svgNode' does not exist on type '{}'.
    svgNode,
  }) => {
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
