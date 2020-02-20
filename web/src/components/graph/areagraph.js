import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
} from 'react';
import { scaleTime, scaleLinear } from 'd3-scale';
import { first, last } from 'lodash';
import moment from 'moment';

import AreaGraphGradients from './areagraphgradients';
import AreaGraphLayers from './areagraphlayers';
import GraphBackground from './graphbackground';
import GraphHoverLine from './graphhoverline';
import ValueAxis from './valueaxis';
import TimeAxis from './timeaxis';

const X_AXIS_HEIGHT = 20;
const Y_AXIS_WIDTH = 35;
const Y_AXIS_PADDING = 4;

const getTimeScale = (containerWidth, datetimes, currentTime) => scaleTime()
  .domain([first(datetimes), currentTime ? moment(currentTime).toDate() : last(datetimes)])
  .range([0, containerWidth]);

const getValueScale = (containerHeight, maxTotalValue) => scaleLinear()
  .domain([0, maxTotalValue * 1.1])
  .range([containerHeight, Y_AXIS_PADDING]);

const AreaGraph = React.memo(({
  id,
  layers,
  currentTime,
  maxTotalValue,
  valueAxisLabel,
  datetimes,
  fillSelector,
  mouseMoveHandler,
  mouseOutHandler,
  layerMouseMoveHandler,
  layerMouseOutHandler,
  selectedTimeIndex,
  selectedLayerIndex,
  gradientIdPrefix,
  gradientLayers,
  gradientStopColorSelector,
  isMobile,
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

  // Generate graph scales
  const timeScale = useMemo(
    () => getTimeScale(container.width, datetimes, currentTime),
    [container.width, datetimes, currentTime]
  );
  const valueScale = useMemo(
    () => getValueScale(container.height, maxTotalValue),
    [container.height, maxTotalValue]
  );

  return (
    <svg id={id} ref={ref}>
      <TimeAxis
        scale={timeScale}
        height={container.height}
      />
      <ValueAxis
        scale={valueScale}
        label={valueAxisLabel}
        width={container.width}
      />
      <GraphBackground
        timeScale={timeScale}
        valueScale={valueScale}
        datetimes={datetimes}
        mouseMoveHandler={mouseMoveHandler}
        mouseOutHandler={mouseOutHandler}
        svgRef={ref}
      />
      <AreaGraphLayers
        layers={layers}
        timeScale={timeScale}
        valueScale={valueScale}
        fillSelector={fillSelector}
        mouseMoveHandler={mouseMoveHandler}
        mouseOutHandler={mouseOutHandler}
        layerMouseMoveHandler={layerMouseMoveHandler}
        layerMouseOutHandler={layerMouseOutHandler}
        isMobile={isMobile}
        svgRef={ref}
      />
      <GraphHoverLine
        timeScale={timeScale}
        valueScale={valueScale}
        datetimes={datetimes}
        fill={selectedLayerIndex && fillSelector(selectedLayerIndex)}
        data={selectedLayerIndex && layers[selectedLayerIndex].data}
        selectedTimeIndex={selectedTimeIndex}
      />
      <AreaGraphGradients
        id={gradientIdPrefix}
        timeScale={timeScale}
        stopColorSelector={gradientStopColorSelector}
        layers={gradientLayers}
      />
    </svg>
  );
});

export default AreaGraph;
