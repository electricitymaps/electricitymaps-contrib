import React, { useState, useEffect, useMemo } from 'react';
import moment from 'moment';
import { connect } from 'react-redux';
import { first, last } from 'lodash';

import formatting from '../helpers/formatting';
import { modeOrder, modeColor } from '../helpers/constants';
import { getCo2Scale } from '../helpers/scales';
import { prepareGraphData } from '../helpers/data';

const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-axis'),
  require('d3-collection'),
  require('d3-scale'),
  require('d3-shape'),
);

const X_AXIS_HEIGHT = 20;
const Y_AXIS_WIDTH = 35;
const Y_AXIS_PADDING = 4;

const Axis = ({
  className,
  label,
  scale,
  renderLine,
  renderTick,
  textAnchor,
  transform,
}) => (
  <g
    className={className}
    transform={transform}
    fill="none"
    fontSize="10"
    fontFamily="sans-serif"
    textAnchor={textAnchor}
    style={{ pointerEvents: 'none' }}
  >
    {label && <text className="label" transform="translate(35, 80) rotate(-90)">{label}</text>}
    <path className="domain" stroke="currentColor" d={renderLine(scale.range())} />
    {scale.ticks(5).map(renderTick)}
  </g>
);

const TimeAxis = React.memo(({ scale, height }) => {
  const renderLine = range => `M${range[0] + 0.5},6V0.5H${range[1] + 0.5}V6`;
  const renderTick = v => (
    <g key={`tick-${v}`} className="tick" opacity={1} transform={`translate(${scale(v)},0)`}>
      <line stroke="currentColor" y2="6" />
      <text fill="currentColor" y="9" dy="0.71em">{moment(v).format('LT')}</text>
    </g>
  );

  return (
    <Axis
      className="x axis"
      scale={scale}
      renderLine={renderLine}
      renderTick={renderTick}
      textAnchor="middle"
      transform={`translate(-1 ${height - X_AXIS_HEIGHT - 1})`}
    />
  );
});

const ValuesAxis = React.memo(({ scale, label, width }) => {
  const renderLine = range => `M6,${range[0] + 0.5}H0.5V${range[1] + 0.5}H6`;
  const renderTick = v => (
    <g key={`tick-${v}`} className="tick" opacity={1} transform={`translate(0,${scale(v)})`}>
      <line stroke="currentColor" x2="6" />
      <text fill="currentColor" x="9" y="3" dx="0.32em">{v}</text>
    </g>
  );

  return (
    <Axis
      className="y axis"
      label={label}
      scale={scale}
      renderLine={renderLine}
      renderTick={renderTick}
      textAnchor="start"
      transform={`translate(${width - Y_AXIS_WIDTH - 1} -1)`}
    />
  );
});

const Graph = React.memo(({
  area,
  datetimes,
  displayByEmissions,
  fillColor,
  stackKeys,
  stackedData,
  timeScale,
  setSelectedLayerIndex,
  mouseMoveHandler,
  mouseOutHandler,
  layerMouseMoveHandler,
  layerMouseOutHandler,
  svgRef,
}) => {
  const detectPosition = (ev) => {
    if (!datetimes.length) return null;
    const dx = ev.pageX
      ? (ev.pageX - svgRef.current.getBoundingClientRect().left)
      : (d3.touches(this)[0][0]);
    const datetime = timeScale.invert(dx);
    // Find data point closest to
    let i = d3.bisectLeft(datetimes, datetime);
    if (i > 0 && datetime - datetimes[i - 1] < datetimes[i] - datetime) i -= 1;
    if (i > datetimes.length - 1) i = datetimes.length - 1;
    return i;
  };

  // Mouse hover events
  let mouseOutTimeout;
  const handleLayerMouseMove = (ev, layer, ind) => {
    if (mouseOutTimeout) {
      clearTimeout(mouseOutTimeout);
      mouseOutTimeout = undefined;
    }
    setSelectedLayerIndex(ind);
    const i = detectPosition(ev);
    if (layerMouseMoveHandler) {
      const position = { x: ev.clientX - 7, y: svgRef.current.getBoundingClientRect().top - 7 };
      layerMouseMoveHandler(stackKeys[ind], position, layer[i].data._countryData);
    }
    if (mouseMoveHandler) {
      mouseMoveHandler(layer[i].data._countryData, i);
    }
  };
  const handleLayerMouseOut = () => {
    mouseOutTimeout = setTimeout(() => {
      setSelectedLayerIndex(undefined);
      if (mouseOutHandler) {
        mouseOutHandler();
      }
      if (layerMouseOutHandler) {
        layerMouseOutHandler();
      }
    }, 50);
  };

  return (
    <g>
      {stackedData.map((layer, ind) => (
        <path
          key={stackKeys[ind]}
          className={`area layer ${stackKeys[ind]}`}
          fill={fillColor(stackKeys[ind], displayByEmissions)}
          d={area(layer)}
          onFocus={ev => handleLayerMouseMove(ev, layer, ind)}
          onMouseOver={ev => handleLayerMouseMove(ev, layer, ind)}
          onMouseMove={ev => handleLayerMouseMove(ev, layer, ind)}
          onMouseOut={handleLayerMouseOut}
          onBlur={handleLayerMouseOut}
        />
      ))}
    </g>
  );
});

const ExchangeLinearGradients = React.memo(({
  colorBlindModeEnabled,
  exchangeKeys,
  graphData,
  timeScale,
}) => {
  const x1 = timeScale.range()[0];
  const x2 = timeScale.range()[1];
  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const stopOffset = datetime => `${(timeScale(datetime) - x1) / (x2 - x1) * 100.0}%`;
  const stopColor = (countryData, key) => (countryData.exchangeCo2Intensities
    ? co2ColorScale(countryData.exchangeCo2Intensities[key]) : 'darkgray');

  return (
    <React.Fragment>
      {exchangeKeys.map(key => (
        <linearGradient gradientUnits="userSpaceOnUse" id={`areagraph-exchange-${key}`} key={key} x1={x1} x2={x2}>
          {graphData.map(d => (
            <stop
              key={d.datetime}
              offset={stopOffset(d.datetime)}
              stopColor={stopColor(d._countryData, key)}
            />
          ))}
        </linearGradient>
      ))}
    </React.Fragment>
  );
});

const getMaxTotalValue = (data, displayByEmissions) =>
  d3.max(data, d => (
    displayByEmissions
      ? (d.totalCo2Production + d.totalCo2Import + d.totalCo2Discharge) / 1e6 / 60.0 // in tCO2eq/min
      : (d.totalProduction + d.totalImport + d.totalDischarge) // in MW
  ));

const getCurrentTime = state =>
  state.application.customDate || (state.data.grid || {}).datetime;

// Regular production mode or exchange fill as a fallback
const fillColor = (key, displayByEmissions) =>
  modeColor[key] || (displayByEmissions ? 'darkgray' : `url(#areagraph-exchange-${key})`);

const getGraphState = (currentTime, data, displayByEmissions, electricityMixMode, width, height) => {
  if (!data || !data[0]) return {};

  let maxTotalValue = getMaxTotalValue(data, displayByEmissions);
  const format = formatting.scalePower(maxTotalValue);
  const formattingFactor = !displayByEmissions ? format.formattingFactor : 1;
  maxTotalValue /= formattingFactor;

  // Prepare graph data
  const {
    datetimes,
    exchangeKeys,
    graphData,
  } = prepareGraphData(data, displayByEmissions, electricityMixMode, formattingFactor);

  // Prepare stack - order is defined here, from bottom to top
  let stackKeys = modeOrder;
  if (electricityMixMode === 'consumption') {
    stackKeys = stackKeys.concat(exchangeKeys);
  }
  const stackedData = d3.stack()
    .offset(d3.stackOffsetDiverging)
    .keys(stackKeys)(graphData);

  // Prepare axes and graph scales
  const timeScale = d3.scaleTime()
    .domain([first(datetimes), currentTime ? moment(currentTime).toDate() : last(datetimes)])
    .range([0, width - Y_AXIS_WIDTH]);
  const valuesScale = d3.scaleLinear()
    .domain([0, maxTotalValue * 1.1])
    .range([height - X_AXIS_HEIGHT, Y_AXIS_PADDING]);
  const area = d3.area()
    .x(d => timeScale(d.data.datetime))
    .y0(d => valuesScale(d[0]))
    .y1(d => valuesScale(d[1]))
    .defined(d => Number.isFinite(d[1]));

  return {
    area,
    datetimes,
    exchangeKeys,
    format,
    graphData,
    timeScale,
    valuesScale,
    stackKeys,
    stackedData,
  };
};

const mapStateToProps = (state, props) => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  // TODO: Check this gets updated regularly
  currentTime: getCurrentTime(state),
  data: props.dataSelector(state),
  displayByEmissions: state.application.tableDisplayEmissions,
  electricityMixMode: state.application.electricityMixMode,
  selectedIndex: state.application.selectedZoneTimeIndex,
});

const AreaGraph = ({
  colorBlindModeEnabled,
  currentTime,
  data,
  displayByEmissions,
  electricityMixMode,
  id,
  selectedIndex,
  layerMouseMoveHandler,
  layerMouseOutHandler,
  mouseMoveHandler,
  mouseOutHandler,
}) => {
  // Hack to create a reference via non-mutable state so that it's created
  // only once at the initialization (like in a class constructor).
  const [ref] = useState(React.createRef());
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(3);
  const [container, setContainer] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const updateDimensions = () => {
      if (ref.current) {
        const { width, height } = ref.current.getBoundingClientRect();
        setContainer({ width, height });
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

  const {
    area,
    datetimes,
    exchangeKeys,
    format,
    graphData,
    timeScale,
    valuesScale,
    stackKeys,
    stackedData,
  } = useMemo(
    () => getGraphState(currentTime, data, displayByEmissions, electricityMixMode, container.width, container.height),
    [currentTime, data, displayByEmissions, electricityMixMode, container.width, container.height]
  );

  if (!data || !data[0]) return null;

  return (
    <svg id={id} ref={ref}>
      <TimeAxis
        scale={timeScale}
        height={container.height}
      />
      <ValuesAxis
        label={displayByEmissions ? 'tCO2eq/min' : format.unit}
        scale={valuesScale}
        width={container.width}
      />
      <Graph
        area={area}
        datetimes={datetimes}
        displayByEmissions={displayByEmissions}
        fillColor={fillColor}
        stackKeys={stackKeys}
        stackedData={stackedData}
        timeScale={timeScale}
        setSelectedLayerIndex={setSelectedLayerIndex}
        mouseMoveHandler={mouseMoveHandler}
        mouseOutHandler={mouseOutHandler}
        layerMouseMoveHandler={layerMouseMoveHandler}
        layerMouseOutHandler={layerMouseOutHandler}
        svgRef={ref}
      />
      {Number.isInteger(selectedIndex) && (
        <line
          className="vertical-line"
          style={{
            display: 'block',
            pointerEvents: 'none',
            shapeRendering: 'crispEdges',
          }}
          x1={timeScale(graphData[selectedIndex].datetime)}
          x2={timeScale(graphData[selectedIndex].datetime)}
          y1={valuesScale.range()[0]}
          y2={valuesScale.range()[1]}
        />
      )}
      {Number.isInteger(selectedIndex) && stackedData[selectedLayerIndex] && (
        <circle
          r="6"
          style={{
            display: 'block',
            pointerEvents: 'none',
            shapeRendering: 'crispEdges',
            stroke: 'black',
            strokeWidth: 1.5,
            fill: fillColor(stackKeys[selectedLayerIndex], displayByEmissions),
          }}
          cx={timeScale(graphData[selectedIndex].datetime)}
          cy={valuesScale(stackedData[selectedLayerIndex][selectedIndex][1])}
        />
      )}
      <ExchangeLinearGradients
        graphData={graphData}
        timeScale={timeScale}
        exchangeKeys={exchangeKeys}
        colorBlindModeEnabled={colorBlindModeEnabled}
      />
    </svg>
  );
};

export default connect(mapStateToProps)(AreaGraph);
