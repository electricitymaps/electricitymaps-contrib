import { ScaleLinear, scaleLinear } from 'd3-scale';
import { Series, stack, stackOffsetDiverging } from 'd3-shape';
import { add } from 'date-fns';
import TimeAxis from 'features/time/TimeAxis';
import { useHeaderHeight } from 'hooks/headerHeight';
import { atom, useAtom, useAtomValue } from 'jotai';
import React, { useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { RouteParameters } from 'types';
import useResizeObserver from 'use-resize-observer';
import { Charts, timeAxisMapping, TimeRange } from 'utils/constants';
import { getZoneTimezone } from 'utils/helpers';
import { selectedDatetimeIndexAtom } from 'utils/state/atoms';
import { useBreakpoint, useIsMobile } from 'utils/styling';

import { getTimeScale } from '../graphUtils';
import { SelectedData } from '../OriginChart';
import AreaGraphTooltip from '../tooltips/AreaGraphTooltip';
import { AreaGraphElement, FillFunction, InnerAreaGraphTooltipProps } from '../types';
import AreaGraphLayers from './AreaGraphLayers';
import GraphBackground from './GraphBackground';
import GraphHoverLine from './GraphHoverline';
import ValueAxis from './ValueAxis';

export const X_AXIS_HEIGHT = 20;
export const Y_AXIS_WIDTH = 26;
export const Y_AXIS_PADDING = 2;

interface Layer {
  key: string;
  stroke: string;
  fill: (d: { data: AreaGraphElement }) => string;
  markerFill: (d: { data: AreaGraphElement }) => string;
  datapoints: Series<AreaGraphElement, string>;
}

const getTotalValues = (layers: Layer[]): { min: number; max: number } => {
  // Use a single loop to find the min and max values of the datapoints
  let min = 0;
  let max = 0;
  for (const layer of layers) {
    for (const [low, high] of layer.datapoints) {
      // Check if the values are finite numbers
      if (Number.isFinite(low)) {
        min = Math.min(min, low);
      }
      if (Number.isFinite(high)) {
        max = Math.max(max, high);
      }
    }
  }
  // Return the min and max values
  return {
    min: min,
    max: max,
  };
};

const getValueScale = (
  height: number,
  totalValues: { min: number; max: number }
): ScaleLinear<number, number> =>
  scaleLinear()
    .domain([Math.min(0, 1.1 * totalValues.min), Math.max(0, 1.1 * totalValues.max)])
    .range([height, Y_AXIS_PADDING]);

const getLayers = (
  data: AreaGraphElement[],
  layerKeys: string[],
  layerFill: FillFunction,
  markerFill?: FillFunction,
  layerStroke?: (key: string) => string
): Layer[] => {
  if (!data || !data[0]) {
    return [];
  }

  const stackedData = stack<AreaGraphElement>()
    .offset(stackOffsetDiverging)
    .value((d: AreaGraphElement, key: string) =>
      Number.isNaN(d.layerData[key]) ? 0 : d.layerData[key]
    ) // Assign 0 if no data
    .keys(layerKeys)(data);

  return layerKeys.map((key: string, index: number) => ({
    key,
    stroke: layerStroke?.(key) ?? 'none',
    fill: layerFill(key),
    markerFill: markerFill?.(key) ?? layerFill(key),
    datapoints: stackedData[index],
  }));
};

interface AreagraphProps {
  id: Charts;
  data: AreaGraphElement[];
  testId: string;
  layerKeys: string[];
  layerStroke?: (key: string) => string;
  layerFill: FillFunction;
  markerFill?: FillFunction;
  markerUpdateHandler: (
    position: { x: number; y: number },
    dataPoint: AreaGraphElement
  ) => void;
  markerHideHandler: () => void;
  isDisabled?: boolean;
  height: string;
  datetimes: Date[];
  selectedTimeRange: TimeRange;
  tooltip: (props: InnerAreaGraphTooltipProps) => JSX.Element | null;
  tooltipSize?: 'small' | 'large';
  formatTick?: (t: number) => string | number;
  isDataInteractive?: boolean;
  selectedData?: SelectedData;
}

const AreaGraphIndexSelectedAtom = atom<number | null>(null);
const AreaGraphHoveredChartAtom = atom<Charts | null>(null);

function AreaGraph({
  id,
  data,
  testId,
  layerKeys,
  layerStroke,
  layerFill,
  markerFill,
  height = '10em',
  isDisabled = false,
  selectedTimeRange,
  datetimes,
  tooltip,
  tooltipSize,
  formatTick = String,
  isDataInteractive = false,
  selectedData,
}: AreagraphProps) {
  const reference = useRef<HTMLDivElement | null>(null);
  const { width: observerWidth = 0, height: observerHeight = 0 } =
    useResizeObserver<HTMLDivElement>({ ref: reference });
  const isMobile = useIsMobile();
  const selectedDate = useAtomValue(selectedDatetimeIndexAtom);
  const [tooltipPosition, setTooltipPosition] = useState<
    { x: number; y: number } | undefined | null
  >(null);
  const isBiggerThanMobile = useBreakpoint('sm');
  const { zoneId } = useParams<RouteParameters>();
  const zoneTimezone = getZoneTimezone(zoneId);

  const containerWidth = Math.max(observerWidth - Y_AXIS_WIDTH, 0);
  const containerHeight = Math.max(observerHeight - X_AXIS_HEIGHT, 0);

  // Build layers
  const layers = useMemo(
    () => getLayers(data, layerKeys, layerFill, markerFill, layerStroke),
    [data, layerKeys, layerStroke, layerFill, markerFill]
  );

  // Generate graph scales
  const totalValues = useMemo(() => getTotalValues(layers), [layers]);
  const valueScale = useMemo(
    () => getValueScale(containerHeight, totalValues),
    [containerHeight, totalValues]
  );
  const startTime = datetimes.at(0);
  const lastTime = datetimes.at(-1);

  // The endTime needs to include the last interval so it can be shown
  const endTime = useMemo(() => {
    if (!lastTime) {
      return null;
    }

    const duration = timeAxisMapping[selectedTimeRange];

    //add exactly 1 interval to the last time, e.g. 1 hour or 1 day or 1 month, etc.
    return add(lastTime, { [duration]: 1 });
  }, [lastTime, selectedTimeRange]);

  const datetimesWithNext = useMemo(
    // The as Date[] assertion is needed because the filter removes the null values but typescript can't infer that
    // This can be inferred by typescript 5.5 and can be removed when we upgrade
    () => [...datetimes, endTime].filter(Boolean) as Date[],
    [datetimes, endTime]
  );

  const timeScale = useMemo(
    () => getTimeScale(containerWidth, startTime, endTime),
    [containerWidth, startTime, endTime]
  );

  const [graphIndex, setGraphIndex] = useAtom(AreaGraphIndexSelectedAtom);
  const [hoveredChart, setHoveredChart] = useAtom(AreaGraphHoveredChartAtom);
  const [hoveredLayerIndex, setHoveredLayerIndex] = useState<number | null>(null);

  const hoverLineTimeIndex = graphIndex ?? selectedDate.index;

  // Mouse action handlers
  const mouseMoveHandler = useMemo(
    () => (timeIndex: number | null, layerIndex: number | null) => {
      setGraphIndex(timeIndex);
      setHoveredChart(id);
      if (layers.length <= 1) {
        // Select the first (and only) layer even when hovering over background
        setHoveredLayerIndex(0);
      } else {
        // use the selected layer (or undefined to hide the tooltips)
        setHoveredLayerIndex(layerIndex);
      }
    },
    [layers, setGraphIndex, setHoveredLayerIndex, id, setHoveredChart]
  );
  const mouseOutHandler = useMemo(
    () => () => {
      if (!isMobile) {
        setGraphIndex(null);
        setHoveredLayerIndex(null);
        setHoveredChart(null);
      }
    },
    [setGraphIndex, setHoveredLayerIndex, isMobile, setHoveredChart]
  );

  const onCloseTooltip = () => {
    setTooltipPosition(null);
    setHoveredLayerIndex(null);
    setGraphIndex(null);
    setHoveredChart(null);
  };

  const headerHeight = useHeaderHeight();

  // Logic for hoverline and marker
  const markerLayer = layers.at(hoveredLayerIndex ?? 0);
  const markerDatapoint = markerLayer?.datapoints?.[hoverLineTimeIndex];
  const nextDateTime = datetimes[hoverLineTimeIndex + 1] ?? endTime;
  const scaledNext = nextDateTime ? timeScale?.(nextDateTime) ?? 0 : 0;
  const selected = timeScale?.(datetimes[hoverLineTimeIndex]) ?? Number.NaN;
  const interval = scaledNext - selected;
  const markerX = selected + interval / 2;
  const markerY = valueScale(
    markerDatapoint?.[markerDatapoint?.[0] < 0 ? 0 : 1] ?? Number.NaN
  );
  const markerLayerFill = markerLayer?.markerFill;
  const markerSafeFill = markerDatapoint
    ? markerLayerFill?.(markerDatapoint) ?? 'none'
    : 'none';
  const markerShowMarker =
    Number.isFinite(markerX) &&
    Number.isFinite(markerY) &&
    id === hoveredChart &&
    Number.isFinite(hoveredLayerIndex);

  // Don't render the graph if datetimes and datapoints are not in sync
  for (const layer of layers) {
    if (layer.datapoints.length !== datetimes.length) {
      console.error('Datetimes and datapoints are not in sync');
      return null;
    }
  }

  if (layers.every((layer) => layer.datapoints.every((d) => d[0] === 0 && d[1] === 0))) {
    // Don't render the graph if all datapoints are 0
    return null;
  }

  return (
    <div ref={reference}>
      <svg
        data-testid={testId}
        height={height}
        className={`w-full overflow-visible ${
          isDisabled ? 'pointer-events-none blur' : ''
        }`}
      >
        {timeScale && reference.current && (
          <GraphBackground
            timeScale={timeScale}
            valueScale={valueScale}
            datetimes={datetimes}
            mouseMoveHandler={mouseMoveHandler}
            mouseOutHandler={mouseOutHandler}
            isMobile={isMobile}
            elementReference={reference.current}
          />
        )}
        <AreaGraphLayers
          isDataInteractive={isDataInteractive}
          hoveredLayerIndex={hoveredLayerIndex}
          selectedData={selectedData}
          layers={layers}
          datetimes={datetimesWithNext}
          timeScale={timeScale}
          valueScale={valueScale}
          mouseMoveHandler={mouseMoveHandler}
          mouseOutHandler={mouseOutHandler}
          isMobile={isMobile}
          svgNode={reference.current}
        />
        <TimeAxis
          isLoading={false}
          selectedTimeRange={selectedTimeRange}
          datetimes={datetimesWithNext}
          scaleWidth={containerWidth}
          transform={`translate(0 ${containerHeight})`}
          className="h-[22px] w-full overflow-visible opacity-50"
          timezone={zoneTimezone}
          chartHeight={containerHeight}
        />
        <ValueAxis scale={valueScale} width={containerWidth} formatTick={formatTick} />
        <GraphHoverLine
          valueScale={valueScale}
          x={markerX}
          y={markerY}
          fill={markerSafeFill}
          showMarker={markerShowMarker}
          setTooltipPosition={setTooltipPosition}
          elementReference={reference.current}
        />
        {tooltip && (
          <AreaGraphTooltip
            zoneDetail={markerDatapoint?.data.meta}
            position={tooltipPosition}
            selectedLayerKey={
              hoveredLayerIndex === null ? undefined : layerKeys[hoveredLayerIndex]
            }
            tooltipSize={tooltipSize}
            isBiggerThanMobile={isBiggerThanMobile}
            headerHeight={headerHeight}
            closeTooltip={onCloseTooltip}
          >
            {(props) => tooltip(props)}
          </AreaGraphTooltip>
        )}
      </svg>
    </div>
  );
}

export default React.memo(AreaGraph);
