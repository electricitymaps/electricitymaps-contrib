import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
} from 'react';
import {
  first,
  last,
  max,
  isNumber,
  isEmpty,
} from 'lodash';
import { scaleTime, scaleLinear } from 'd3-scale';
import { stack, stackOffsetDiverging } from 'd3-shape';
import moment from 'moment';

import AreaGraphLayers from './areagraphlayers';
import GraphBackground from './graphbackground';
import GraphHoverLine from './graphhoverline';
import ValueAxis from './valueaxis';
import TimeAxis from './timeaxis';

const X_AXIS_HEIGHT = 20;
const Y_AXIS_WIDTH = 40;
const Y_AXIS_PADDING = 4;

const getDatetimes = data => (data || []).map(d => d.datetime);

const getTimeScale = (containerWidth, datetimes, startTime, endTime) => scaleTime()
  .domain([
    startTime ? moment(startTime).toDate() : first(datetimes),
    endTime ? moment(endTime).toDate() : last(datetimes),
  ])
  .range([0, containerWidth]);

const getMaxTotalValue = layers => (last(layers) ? max(last(layers).datapoints.map(d => d[1])) : 0);

const getValueScale = (containerHeight, maxTotalValue) => scaleLinear()
  .domain([0, maxTotalValue * 1.1])
  .range([containerHeight, Y_AXIS_PADDING]);

const getLayers = (data, layerKeys, layerStroke, layerFill, markerFill) => {
  if (!data || !data[0]) return [];
  const stackedData = stack()
    .offset(stackOffsetDiverging)
    .keys(layerKeys)(data);
  return layerKeys.map((key, ind) => ({
    key,
    stroke: layerStroke ? layerStroke(key) : 'none',
    fill: layerFill(key),
    markerFill: markerFill ? markerFill(key) : layerFill(key),
    datapoints: stackedData[ind],
  }));
};

const AreaGraph = React.memo(({
  /*
    `data` should be an array of objects, each containing:
      * a numerical value for every key appearing in `layerKeys`
      * `datetime` timestamp
  */
  data,
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
    `startTime` and `endTime` are timestamps denoting the time interval of the rendered part of the graph.
    If not provided, they'll be inferred from timestamps of the first/last datapoints.
  */
  startTime,
  endTime,
  /*
    `valueAxisLabel` is a string label for the values (Y-axis) scale.
  */
  valueAxisLabel,
  /*
    Mouse event callbacks for the graph background and individual layers respectively.
  */
  backgroundMouseMoveHandler,
  backgroundMouseOutHandler,
  layerMouseMoveHandler,
  layerMouseOutHandler,
  /*
    `selectedTimeIndex` is am integer value representing the time index of the datapoint in focus.
  */
  selectedTimeIndex,
  /*
    `selectedLayerIndex` is an integer value representing the layer index of the datapoint in focus.
  */
  selectedLayerIndex,
  /*
    If `isMobile` is true, the mouse hover events are triggered by clicks only.
  */
  isMobile,
  /*
    Height of the area graph canvas.
  */
  height = '10em',
}) => {
  const ref = useRef(null);
  const [container, setContainer] = useState({ width: 0, height: 0 });

  // Container resize hook
  useEffect(() => {
    const updateDimensions = () => {
      if (ref.current) {
        setContainer({
          width: ref.current.getBoundingClientRect().width - Y_AXIS_WIDTH,
          height: ref.current.getBoundingClientRect().height - X_AXIS_HEIGHT,
        });
      }
    };
    // Initialize dimensions if they are not set yet
    if (!container.width || !container.height) {
      updateDimensions();
    }
    // Update container dimensions on every resize
    window.addEventListener('resize', updateDimensions);
    return () => {
      window.removeEventListener('resize', updateDimensions);
    };
  });

  // Build layers
  const layers = useMemo(
    () => getLayers(data, layerKeys, layerStroke, layerFill, markerFill),
    [data, layerKeys, layerStroke, layerFill, markerFill]
  );

  // Generate graph scales
  const maxTotalValue = useMemo(() => getMaxTotalValue(layers), [layers]);
  const valueScale = useMemo(
    () => getValueScale(container.height, maxTotalValue),
    [container.height, maxTotalValue]
  );
  const datetimes = useMemo(() => getDatetimes(data), [data]);
  const timeScale = useMemo(
    () => getTimeScale(container.width, datetimes, startTime, endTime),
    [container.width, datetimes, startTime, endTime]
  );

  // Don't render the graph at all if no layers are present
  if (isEmpty(layers)) return null;

  return (
    <svg height={height} style={{ overflow: 'visible' }} ref={ref}>
      <TimeAxis
        scale={timeScale}
        transform={`translate(-1 ${container.height - 1})`}
        className="x axis"
      />
      <ValueAxis
        scale={valueScale}
        label={valueAxisLabel}
        width={container.width}
        height={container.height}
      />
      <GraphBackground
        layers={layers}
        timeScale={timeScale}
        valueScale={valueScale}
        datetimes={datetimes}
        mouseMoveHandler={backgroundMouseMoveHandler}
        mouseOutHandler={backgroundMouseOutHandler}
        isMobile={isMobile}
        svgRef={ref}
      />
      <AreaGraphLayers
        layers={layers}
        datetimes={datetimes}
        timeScale={timeScale}
        valueScale={valueScale}
        mouseMoveHandler={layerMouseMoveHandler}
        mouseOutHandler={layerMouseOutHandler}
        isMobile={isMobile}
        svgRef={ref}
      />
      <GraphHoverLine
        timeScale={timeScale}
        valueScale={valueScale}
        datetimes={datetimes}
        fill={isNumber(selectedLayerIndex) && layers[selectedLayerIndex].markerFill}
        data={isNumber(selectedLayerIndex) && layers[selectedLayerIndex].datapoints}
        selectedTimeIndex={selectedTimeIndex}
      />
    </svg>
  );
});

export default AreaGraph;
