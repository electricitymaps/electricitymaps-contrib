import React, { useState, useEffect, useRef } from 'react';
import { scaleTime, scaleLinear } from 'd3-scale';
import { first, last } from 'lodash';
import moment from 'moment';

import AreaGraphLayers from './areagraphlayers';
import GraphBackground from './graphbackground';
import GraphHoverLine from './graphhoverline';
import ValueAxis from './valueaxis';
import TimeAxis from './timeaxis';

const X_AXIS_HEIGHT = 20;
const Y_AXIS_WIDTH = 35;
const Y_AXIS_PADDING = 4;

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
  renderGradients,
  isMobile,
}) => {
  const ref = useRef(null);
  const [container, setContainer] = useState({ width: 0, height: 0 });

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

  // Prepare axes and graph scales
  const timeScale = scaleTime()
    .domain([first(datetimes), currentTime ? moment(currentTime).toDate() : last(datetimes)])
    .range([0, container.width]);
  const valueScale = scaleLinear()
    .domain([0, maxTotalValue * 1.1])
    .range([container.height, Y_AXIS_PADDING]);

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
      {renderGradients && renderGradients(timeScale)}
    </svg>
  );
});

export default AreaGraph;
