import React, { useEffect } from 'react';
import { isFinite, isFunction } from 'lodash';

const GraphHoverLine = React.memo(({
  layers,
  datetimes,
  timeScale,
  valueScale,
  markerUpdateHandler,
  markerHideHandler,
  selectedLayerIndex,
  selectedTimeIndex,
  svgRef,
}) => {
  const layer = layers && layers[selectedLayerIndex];
  const fill = layer && layer.markerFill;
  const datapoint = layer && layer.datapoints && layer.datapoints[selectedTimeIndex];

  const x = datetimes && datetimes[selectedTimeIndex] && timeScale(datetimes[selectedTimeIndex]);
  const y = datapoint && isFinite(datapoint[1]) && valueScale(datapoint[1]);

  const showVerticalLine = isFinite(x);
  const showMarker = isFinite(x) && isFinite(y);

  // Marker callbacks
  useEffect(() => {
    if (showMarker) {
      if (markerUpdateHandler && svgRef.current) {
        markerUpdateHandler(
          {
            x: svgRef.current.getBoundingClientRect().left + x,
            y: svgRef.current.getBoundingClientRect().top + y,
          },
          datapoint.data,
          layer.key,
        );
      }
    } else if (markerHideHandler) {
      markerHideHandler();
    }
  }, [markerUpdateHandler, markerHideHandler, svgRef.current, showMarker, x, y, datapoint, layer]);

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
            fill: isFunction(fill) ? fill(datapoint) : fill,
          }}
          cx={x}
          cy={y}
        />
      )}
    </React.Fragment>
  );
});

export default GraphHoverLine;
