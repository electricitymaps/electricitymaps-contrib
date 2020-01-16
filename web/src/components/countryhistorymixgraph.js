import React, { useState, useMemo } from 'react';
import { stack, stackOffsetDiverging } from 'd3-shape';
import { max as d3Max } from 'd3-array';
import { connect } from 'react-redux';

import formatting from '../helpers/formatting';
import { getCo2Scale } from '../helpers/scales';
import { modeOrder, modeColor } from '../helpers/constants';
import { prepareGraphData } from '../helpers/data';
import { dispatchApplication } from '../store';

import AreaGraphGradients from './graph/areagraphgradients';
import AreaGraph from './graph/areagraph';

const getValuesInfo = (data, displayByEmissions) => {
  let maxTotalValue = d3Max(data, d => (
    displayByEmissions
      ? (d.totalCo2Production + d.totalCo2Import + d.totalCo2Discharge) / 1e6 / 60.0 // in tCO2eq/min
      : (d.totalProduction + d.totalImport + d.totalDischarge) // in MW
  ));
  const format = formatting.scalePower(maxTotalValue);
  const formattingFactor = !displayByEmissions ? format.formattingFactor : 1;
  maxTotalValue /= formattingFactor;

  const valueUnit = format.unit;
  const valueFactor = format.formattingFactor;
  return { maxTotalValue, valueUnit, valueFactor };
};

// TODO: Consider merging this method with prepareGraphData.
// This method is consumed by the CountryHistoryMixGraph component in such a way that it only gets
// called if one of its input parameters changes. So recalculation doesn't happen if a user e.g.
// hovers over the graph triggering a tooltip.
const getGraphState = (currentTime, data, displayByEmissions, electricityMixMode) => {
  if (!data || !data[0]) return {};

  // Prepare graph data
  const { maxTotalValue, valueUnit, valueFactor } = getValuesInfo(data, displayByEmissions);
  const { exchangeKeys, graphData } = prepareGraphData(data, displayByEmissions, electricityMixMode, valueFactor);

  // Prepare stack - order is defined here, from bottom to top
  const stackKeys = modeOrder.concat(electricityMixMode === 'consumption' ? exchangeKeys : []);
  const stackedData = stack()
    .offset(stackOffsetDiverging)
    .keys(stackKeys)(graphData);

  const datetimes = graphData.map(d => d.datetime);
  const layers = stackKeys.map((key, ind) => ({ key, data: stackedData[ind] }));
  const exchangeLayers = layers.filter(layer => exchangeKeys.includes(layer.key));

  return {
    datetimes,
    valueUnit,
    layers,
    exchangeLayers,
    maxTotalValue,
  };
};

const getCurrentTime = state =>
  state.application.customDate || (state.data.grid || {}).datetime;

const getSelectedZoneHistories = state =>
  state.data.histories[state.application.selectedZoneName];

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  currentTime: getCurrentTime(state),
  data: getSelectedZoneHistories(state),
  displayByEmissions: state.application.tableDisplayEmissions,
  electricityMixMode: state.application.electricityMixMode,
  isMobile: state.application.isMobile,
  selectedTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryHistoryMixGraph = ({
  colorBlindModeEnabled,
  currentTime,
  data,
  displayByEmissions,
  electricityMixMode,
  isMobile,
  selectedTimeIndex,
}) => {
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);

  const {
    datetimes,
    valueUnit,
    layers,
    exchangeLayers,
    maxTotalValue,
  } = useMemo(
    () => getGraphState(currentTime, data, displayByEmissions, electricityMixMode),
    [currentTime, data, displayByEmissions, electricityMixMode]
  );

  if (!data || !data[0]) return null;

  const mouseMoveHandler = (timeIndex) => {
    dispatchApplication('selectedZoneTimeIndex', timeIndex);
  };
  const mouseOutHandler = () => {
    dispatchApplication('selectedZoneTimeIndex', null);
  };
  const layerMouseMoveHandler = (timeIndex, layerIndex, layer, ev, svgRef) => {
    // If in mobile mode, put the tooltip to the top of the screen for
    // readability, otherwise float it depending on the cursor position.
    const tooltipPosition = !isMobile
      ? { x: ev.clientX - 7, y: svgRef.current.getBoundingClientRect().top - 7 }
      : { x: 0, y: 0 };
    setSelectedLayerIndex(layerIndex);
    dispatchApplication('selectedZoneTimeIndex', timeIndex);
    dispatchApplication('tooltipDisplayMode', layer.key);
    dispatchApplication('tooltipPosition', tooltipPosition);
    dispatchApplication('tooltipZoneData', layer.data[timeIndex].data._countryData);
  };
  const layerMouseOutHandler = () => {
    setSelectedLayerIndex(null);
    dispatchApplication('tooltipDisplayMode', null);
  };

  const valueAxisLabel = displayByEmissions ? 'tCO2eq/min' : valueUnit;

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const gradientStopColor = (d, key) => (d._countryData.exchangeCo2Intensities
    ? co2ColorScale(d._countryData.exchangeCo2Intensities[key]) : 'darkgray');

  // Regular production mode fill or exchange fill as a fallback
  const fillSelector = layerIndex => modeColor[layers[layerIndex].key]
    || (displayByEmissions ? 'darkgray' : `url(#areagraph-exchange-${layers[layerIndex].key})`);

  const renderGradients = timeScale => (
    <AreaGraphGradients
      id="areagraph-exchange"
      timeScale={timeScale}
      stopColor={gradientStopColor}
      layers={exchangeLayers}
    />
  );

  return (
    <AreaGraph
      id="country-history-mix"
      layers={layers}
      currentTime={currentTime}
      maxTotalValue={maxTotalValue}
      valueAxisLabel={valueAxisLabel}
      datetimes={datetimes}
      fillSelector={fillSelector}
      mouseMoveHandler={mouseMoveHandler}
      mouseOutHandler={mouseOutHandler}
      layerMouseMoveHandler={layerMouseMoveHandler}
      layerMouseOutHandler={layerMouseOutHandler}
      selectedTimeIndex={selectedTimeIndex}
      selectedLayerIndex={selectedLayerIndex}
      renderGradients={renderGradients}
      isMobile={isMobile}
    />
  );
};

export default connect(mapStateToProps)(CountryHistoryMixGraph);
