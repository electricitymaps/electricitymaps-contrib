import React, { useMemo, useState } from 'react';
import { scaleTime, scaleLinear } from 'd3-scale';
import { stack, stackOffsetDiverging } from 'd3-shape';

import { isEmpty } from '../../helpers/isEmpty';

import AreaGraphLayers from './areagraphlayers';
import GraphBackground from './graphbackground';
import GraphHoverLine from './graphhoverline';
import ValueAxis from './valueaxis';
import TimeAxis from './timeaxis';
import { useRefWidthHeightObserver } from '../../hooks/viewport';
import { useCurrentZoneHistoryDatetimes } from '../../hooks/redux';

import { useSelector } from 'react-redux';

const X_AXIS_HEIGHT = 20;
const Y_AXIS_WIDTH = 40;
const Y_AXIS_PADDING = 4;

const getTimeScale = (width, startTime, endTime) =>
  scaleTime()
    .domain([new Date(startTime), new Date(endTime)])
    .range([0, width]);

const getTotalValues = (layers) => {
  const values = layers.flatMap((layer) => layer.datapoints.map((d) => d[1])).filter(Number.isFinite);

  return {
    min: Number.isFinite(Math.min(...values)) ? Math.min(...values) : 0,
    max: Number.isFinite(Math.max(...values)) ? Math.max(...values) : 0,
  };
};

const getValueScale = (height, totalValues) =>
  scaleLinear()
    .domain([Math.min(0, 1.1 * totalValues.min), Math.max(0, 1.1 * totalValues.max)])
    .range([height, Y_AXIS_PADDING]);

const getLayers = (data, layerKeys, layerStroke, layerFill, markerFill) => {
  if (!data || !data[0]) {
    return [];
  }

  const stackedData = stack()
    .offset(stackOffsetDiverging)
    .value((d, key) => (d[key] === null ? undefined : d[key]))
    .keys(layerKeys)(data);
  return layerKeys.map((key, ind) => ({
    key,
    stroke: layerStroke ? layerStroke(key) : 'none',
    fill: layerFill(key),
    markerFill: markerFill ? markerFill(key) : layerFill(key),
    datapoints: stackedData[ind],
  }));
};

const AreaGraph = React.memo(
  ({
    /*
    `data` should be an array of objects, each containing:
      * a numerical value for every key appearing in `layerKeys`
      * `datetime` timestamp
  */
    data,
    testId,
    /*
    `layerKey` should be an array of strings denoting the graph layers (in bottom-to-top order).
  */
    layerKeys,
    /*
    `layerStroke` should be a function mapping each layer key into a string value representing the layer's stroke color.
  */
    layerStroke,
    /*
    `layerFill` should be a function that maps each layer key into one of the following:
      * a string value representing the layer's fill color if it's homogenous
      * a function mapping each layer's data point to a string color value, rendering a horizontal gradient
  */
    layerFill,
    /*
    `markerFill` is an optional prop of that same format that overrides `layerFill` for the graph focal point fill.
  */
    markerFill,
    /*
    `valueAxisLabel` is a string label for the values (Y-axis) scale.
  */
    valueAxisLabel,
    /*
    Marker hooks that get called when the marker selection gets updated or hidden
  */
    markerUpdateHandler,
    markerHideHandler,
    /*
    If `isMobile` is true, the mouse hover events are triggered by clicks only.
  */
    isMobile,
    /*
    Height of the area graph canvas.
  */
    height = '10em',
  }) => {
    const {
      ref,
      width: containerWidth,
      height: containerHeight,
      node,
    } = useRefWidthHeightObserver(Y_AXIS_WIDTH, X_AXIS_HEIGHT);

    // Build layers
    const layers = useMemo(
      () => getLayers(data, layerKeys, layerStroke, layerFill, markerFill),
      [data, layerKeys, layerStroke, layerFill, markerFill]
    );

    // Generate graph scales
    const totalValues = useMemo(() => getTotalValues(layers), [layers]);
    const valueScale = useMemo(() => getValueScale(containerHeight, totalValues), [containerHeight, totalValues]);
    const datetimes = useCurrentZoneHistoryDatetimes();
    const startTime = datetimes.at(0);
    const endTime = datetimes.at(-1);

    const timeScale = useMemo(
      () => getTimeScale(containerWidth, startTime, endTime),
      [containerWidth, startTime, endTime]
    );

    const selectedTimeAggregate = useSelector((state) => state.application.selectedTimeAggregate);

    const [graphIndex, setGraphIndex] = useState(null);
    const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);

    // Mouse action handlers
    const mouseMoveHandler = useMemo(
      () => (timeIndex, layerIndex) => {
        setGraphIndex(timeIndex);
        if (layers.length <= 1) {
          // Select the first (and only) layer even when hovering over background
          setSelectedLayerIndex(0);
        } else {
          // use the selected layer (or undefined to hide the tooltips)
          setSelectedLayerIndex(layerIndex);
        }
      },
      [layers, setGraphIndex, setSelectedLayerIndex]
    );
    const mouseOutHandler = useMemo(
      () => () => {
        setGraphIndex(null);
        setSelectedLayerIndex(null);
      },
      [setGraphIndex, setSelectedLayerIndex]
    );

    // Don't render the graph at all if no layers are present
    if (isEmpty(layers)) {
      return null;
    }

    return (
      <svg data-test-id={testId} height={height} ref={ref} style={{ overflow: 'visible' }}>
        <GraphBackground
          timeScale={timeScale}
          valueScale={valueScale}
          datetimes={datetimes}
          mouseMoveHandler={mouseMoveHandler}
          mouseOutHandler={mouseOutHandler}
          isMobile={isMobile}
          svgNode={node}
        />
        <AreaGraphLayers
          layers={layers}
          datetimes={datetimes}
          timeScale={timeScale}
          valueScale={valueScale}
          mouseMoveHandler={mouseMoveHandler}
          mouseOutHandler={mouseOutHandler}
          isMobile={isMobile}
          svgNode={node}
        />
        <TimeAxis
          scale={timeScale}
          transform={`translate(-1 ${containerHeight - 1})`}
          className="x axis"
          selectedTimeAggregate={selectedTimeAggregate}
          datetimes={datetimes}
        />
        <ValueAxis scale={valueScale} label={valueAxisLabel} width={containerWidth} height={containerHeight} />
        <GraphHoverLine
          layers={layers}
          timeScale={timeScale}
          valueScale={valueScale}
          datetimes={datetimes}
          markerUpdateHandler={markerUpdateHandler}
          markerHideHandler={markerHideHandler}
          selectedLayerIndex={selectedLayerIndex}
          selectedTimeIndex={graphIndex}
          svgNode={node}
        />
      </svg>
    );
  }
);

export default AreaGraph;
