import React, {
  useState,
  useEffect,
  useMemo,
  useRef,
} from 'react';
import moment from 'moment';
import { connect } from 'react-redux';
import { first, last } from 'lodash';

import formatting from '../helpers/formatting';
import { modeOrder, modeColor } from '../helpers/constants';
import { prepareGraphData } from '../helpers/data';
import { dispatchApplication } from '../store';

import CountryHistoryExchangeGradients from './countryhistoryexchangegradients';
import CountryHistoryMixLayers from './countryhistorymixlayers';
import InteractionBackground from './graph/interactionbackground';
import HoverLine from './graph/hoverline';
import ValueAxis from './graph/valueaxis';
import TimeAxis from './graph/timeaxis';

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

const dataSelector = state =>
  state.data.histories[state.application.selectedZoneName];

const mouseMoveHandler = (countryData, index) => {
  dispatchApplication('selectedZoneTimeIndex', index);
};
const mouseOutHandler = () => {
  dispatchApplication('selectedZoneTimeIndex', null);
};
const layerMouseMoveHandler = (mode, position, zoneData, index) => {
  dispatchApplication('tooltipDisplayMode', mode);
  dispatchApplication('tooltipPosition', position);
  dispatchApplication('tooltipZoneData', zoneData);
  dispatchApplication('selectedZoneTimeIndex', index);
};
const layerMouseOutHandler = () => {
  dispatchApplication('tooltipDisplayMode', null);
};

// TODO: Consider merging this method with prepareGraphData.
// This method is consumed by the AreaGraph component in such a way that it only gets called
// if one of its input parameters changes. So recalculation doesn't happen if a user e.g. hovers
// over the graph triggering a tooltip.
const getGraphState = (currentTime, data, displayByEmissions, electricityMixMode, width, height) => {
  if (!data || !data[0]) return {};

  let maxTotalValue = d3.max(data, d => (
    displayByEmissions
      ? (d.totalCo2Production + d.totalCo2Import + d.totalCo2Discharge) / 1e6 / 60.0 // in tCO2eq/min
      : (d.totalProduction + d.totalImport + d.totalDischarge) // in MW
  ));
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
    .range([0, width]);
  const valueScale = d3.scaleLinear()
    .domain([0, maxTotalValue * 1.1])
    .range([height, Y_AXIS_PADDING]);

  return {
    datetimes,
    exchangeKeys,
    format,
    graphData,
    timeScale,
    valueScale,
    stackKeys,
    stackedData,
  };
};

const getCurrentTime = state =>
  state.application.customDate || (state.data.grid || {}).datetime;

// Regular production mode or exchange fill as a fallback
const fillColor = (key, displayByEmissions) =>
  modeColor[key] || (displayByEmissions ? 'darkgray' : `url(#areagraph-exchange-${key})`);

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  currentTime: getCurrentTime(state),
  data: dataSelector(state),
  displayByEmissions: state.application.tableDisplayEmissions,
  electricityMixMode: state.application.electricityMixMode,
  isMobile: state.application.isMobile,
  selectedIndex: state.application.selectedZoneTimeIndex,
});

const CountryHistoryMixGraph = ({
  colorBlindModeEnabled,
  currentTime,
  data,
  displayByEmissions,
  electricityMixMode,
  isMobile,
  selectedIndex,
}) => {
  const ref = useRef(null);
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);
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

  const {
    datetimes,
    exchangeKeys,
    format,
    graphData,
    timeScale,
    valueScale,
    stackKeys,
    stackedData,
  } = useMemo(
    () => getGraphState(currentTime, data, displayByEmissions, electricityMixMode, container.width, container.height),
    [currentTime, data, displayByEmissions, electricityMixMode, container.width, container.height]
  );

  if (!data || !data[0]) return null;

  return (
    <svg id="country-history-mix" ref={ref}>
      <TimeAxis
        scale={timeScale}
        height={container.height}
      />
      <ValueAxis
        label={displayByEmissions ? 'tCO2eq/min' : format.unit}
        scale={valueScale}
        width={container.width}
      />
      <InteractionBackground
        timeScale={timeScale}
        valueScale={valueScale}
        datetimes={datetimes}
        mouseMoveHandler={mouseMoveHandler}
        mouseOutHandler={mouseOutHandler}
        svgRef={ref}
      />
      <CountryHistoryMixLayers
        fillColor={fillColor}
        stackKeys={stackKeys}
        stackedData={stackedData}
        timeScale={timeScale}
        valueScale={valueScale}
        setSelectedLayerIndex={setSelectedLayerIndex}
        mouseMoveHandler={mouseMoveHandler}
        mouseOutHandler={mouseOutHandler}
        layerMouseMoveHandler={layerMouseMoveHandler}
        layerMouseOutHandler={layerMouseOutHandler}
        svgRef={ref}
      />
      <HoverLine
        graphData={graphData}
        layerData={stackedData[selectedLayerIndex]}
        fill={fillColor(stackKeys[selectedLayerIndex], displayByEmissions)}
        selectedIndex={selectedIndex}
        valueScale={valueScale}
        timeScale={timeScale}
      />
      <CountryHistoryExchangeGradients
        graphData={graphData}
        timeScale={timeScale}
        exchangeKeys={exchangeKeys}
      />
    </svg>
  );
};

export default connect(mapStateToProps)(CountryHistoryMixGraph);
