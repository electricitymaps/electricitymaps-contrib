import React, { useMemo, useState } from 'react';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'd3-s... Remove this comment to see the full error message
import { scaleTime, scaleLinear } from 'd3-scale';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'd3-s... Remove this comment to see the full error message
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

const getTimeScale = (width: any, startTime: any, endTime: any) =>
  scaleTime()
    .domain([new Date(startTime), new Date(endTime)])
    .range([0, width]);

const getTotalValues = (layers: any) => {
  const values = layers.flatMap((layer: any) => layer.datapoints.map((d: any) => d[1])).filter(Number.isFinite);

  return {
    min: Number.isFinite(Math.min(...values)) ? Math.min(...values) : 0,
    max: Number.isFinite(Math.max(...values)) ? Math.max(...values) : 0,
  };
};

const getValueScale = (height: any, totalValues: any) =>
  scaleLinear()
    .domain([Math.min(0, 1.1 * totalValues.min), Math.max(0, 1.1 * totalValues.max)])
    .range([height, Y_AXIS_PADDING]);

const getLayers = (data: any, layerKeys: any, layerStroke: any, layerFill: any, markerFill: any) => {
  if (!data || !data[0]) {
    return [];
  }

  const stackedData = stack()
    .offset(stackOffsetDiverging)
    .value((d: any, key: any) => (d[key] === null ? undefined : d[key]))
    .keys(layerKeys)(data);
  // @ts-expect-error TS(7006): Parameter 'key' implicitly has an 'any' type.
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
    // @ts-expect-error TS(2339): Property 'data' does not exist on type '{}'.
    data,
    // @ts-expect-error TS(2339): Property 'testId' does not exist on type '{}'.
    testId,
    /*
    `layerKey` should be an array of strings denoting the graph layers (in bottom-to-top order).
  */
    // @ts-expect-error TS(2339): Property 'layerKeys' does not exist on type '{}'.
    layerKeys,
    /*
    `layerStroke` should be a function mapping each layer key into a string value representing the layer's stroke color.
  */
    // @ts-expect-error TS(2339): Property 'layerStroke' does not exist on type '{}'... Remove this comment to see the full error message
    layerStroke,
    /*
    `layerFill` should be a function that maps each layer key into one of the following:
      * a string value representing the layer's fill color if it's homogenous
      * a function mapping each layer's data point to a string color value, rendering a horizontal gradient
  */
    // @ts-expect-error TS(2339): Property 'layerFill' does not exist on type '{}'.
    layerFill,
    /*
    `markerFill` is an optional prop of that same format that overrides `layerFill` for the graph focal point fill.
  */
    // @ts-expect-error TS(2339): Property 'markerFill' does not exist on type '{}'.
    markerFill,
    /*
    `valueAxisLabel` is a string label for the values (Y-axis) scale.
  */
    // @ts-expect-error TS(2339): Property 'valueAxisLabel' does not exist on type '... Remove this comment to see the full error message
    valueAxisLabel,
    /*
    Marker hooks that get called when the marker selection gets updated or hidden
  */
    // @ts-expect-error TS(2339): Property 'markerUpdateHandler' does not exist on t... Remove this comment to see the full error message
    markerUpdateHandler,
    // @ts-expect-error TS(2339): Property 'markerHideHandler' does not exist on typ... Remove this comment to see the full error message
    markerHideHandler,
    /*
    If `isMobile` is true, the mouse hover events are triggered by clicks only.
  */
    // @ts-expect-error TS(2339): Property 'isMobile' does not exist on type '{}'.
    isMobile,
    /*
    Height of the area graph canvas.
  */
    // @ts-expect-error TS(2339): Property 'height' does not exist on type '{}'.
    height = '10em',
    // @ts-expect-error TS(2339): Property 'isOverlayEnabled' does not exist on type... Remove this comment to see the full error message
    isOverlayEnabled,
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
    const lastTime = datetimes.at(-1);
    const intervalMs = datetimes.length > 1 ? lastTime.getTime() - datetimes.at(-2).getTime() : undefined;
    // The endTime needs to include the last interval so it can be shown
    const endTime = useMemo(() => new Date(lastTime.getTime() + intervalMs), [lastTime, intervalMs]);
    const datetimesWithNext = useMemo(() => [...datetimes, endTime], [datetimes, endTime]);

    const timeScale = useMemo(
      () => getTimeScale(containerWidth, startTime, endTime),
      [containerWidth, startTime, endTime]
    );

    const selectedTimeAggregate = useSelector((state) => (state as any).application.selectedTimeAggregate);
    const selectedZoneTimeIndex = useSelector((state) => (state as any).application.selectedZoneTimeIndex);

    const [graphIndex, setGraphIndex] = useState(null);
    const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);

    const hoverLineTimeIndex = graphIndex ?? selectedZoneTimeIndex;

    // Mouse action handlers
    const mouseMoveHandler = useMemo(
      () => (timeIndex: any, layerIndex: any) => {
        setGraphIndex(timeIndex);
        if (layers.length <= 1) {
          // Select the first (and only) layer even when hovering over background
          // @ts-expect-error TS(2345): Argument of type '0' is not assignable to paramete... Remove this comment to see the full error message
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
          // @ts-expect-error TS(2322): Type '{ timeScale: any; valueScale: any; datetimes... Remove this comment to see the full error message
          timeScale={timeScale}
          valueScale={valueScale}
          datetimes={datetimes}
          mouseMoveHandler={mouseMoveHandler}
          mouseOutHandler={mouseOutHandler}
          isMobile={isMobile}
          svgNode={node}
        />
        <AreaGraphLayers
          // @ts-expect-error TS(2322): Type '{ layers: any; datetimes: any[]; timeScale: ... Remove this comment to see the full error message
          layers={layers}
          datetimes={datetimesWithNext}
          timeScale={timeScale}
          valueScale={valueScale}
          mouseMoveHandler={mouseMoveHandler}
          mouseOutHandler={mouseOutHandler}
          isMobile={isMobile}
          svgNode={node}
        />
        {!isOverlayEnabled && (
          <TimeAxis
            // @ts-expect-error TS(2322): Type '{ scale: any; transform: string; className: ... Remove this comment to see the full error message
            scale={timeScale}
            transform={`translate(-1 ${containerHeight - 1})`}
            className="x axis"
            selectedTimeAggregate={selectedTimeAggregate}
            datetimes={datetimesWithNext}
          />
        )}
        {/* @ts-expect-error TS(2322): Type '{ scale: any; label: any; width: number; hei... Remove this comment to see the full error message */}
        <ValueAxis scale={valueScale} label={valueAxisLabel} width={containerWidth} height={containerHeight} />
        <GraphHoverLine
          // @ts-expect-error TS(2322): Type '{ layers: any; timeScale: any; valueScale: a... Remove this comment to see the full error message
          layers={layers}
          timeScale={timeScale}
          valueScale={valueScale}
          datetimes={datetimes}
          markerUpdateHandler={markerUpdateHandler}
          markerHideHandler={markerHideHandler}
          selectedLayerIndex={selectedLayerIndex}
          selectedTimeIndex={hoverLineTimeIndex}
          svgNode={node}
        />
      </svg>
    );
  }
);

export default AreaGraph;
