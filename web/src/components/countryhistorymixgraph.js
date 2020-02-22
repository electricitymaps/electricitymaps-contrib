import moment from 'moment';
import React, { useState, useMemo, useCallback } from 'react';
import { stack, stackOffsetDiverging } from 'd3-shape';
import { max as d3Max } from 'd3-array';
import { connect } from 'react-redux';
import { forEach } from 'lodash';

import formatting from '../helpers/formatting';
import { getCo2Scale } from '../helpers/scales';
import { modeOrder, modeColor } from '../helpers/constants';
import { getExchangeKeys } from '../helpers/redux';
import { dispatchApplication } from '../store';

import AreaGraph from './graph/areagraph';

const getValuesInfo = (historyData, displayByEmissions) => {
  let maxTotalValue = d3Max(historyData, d => (
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

const getGraphState = (currentTime, historyData, displayByEmissions, electricityMixMode) => {
  if (!historyData || !historyData[0]) return {};

  // Prepare graph data
  const { maxTotalValue, valueUnit, valueFactor } = getValuesInfo(historyData, displayByEmissions);
  const graphData = historyData.map((d) => {
    // TODO: Simplify this function and make it more readable
    const obj = {
      datetime: moment(d.stateDatetime).toDate(),
    };
    // Add production
    modeOrder.forEach((k) => {
      const isStorage = k.indexOf('storage') !== -1;
      const value = isStorage
        ? -1 * Math.min(0, (d.storage || {})[k.replace(' storage', '')])
        : (d.production || {})[k];
      // in GW or MW
      obj[k] = value / valueFactor;
      if (Number.isFinite(value) && displayByEmissions && obj[k] != null) {
        // in tCO2eq/min
        if (isStorage && obj[k] >= 0) {
          obj[k] *= d.dischargeCo2Intensities[k.replace(' storage', '')] / 1e3 / 60.0;
        } else {
          obj[k] *= d.productionCo2Intensities[k] / 1e3 / 60.0;
        }
      }
    });
    if (electricityMixMode === 'consumption') {
      // Add exchange
      forEach(d.exchange, (value, key) => {
        // in GW or MW
        obj[key] = Math.max(0, value / valueFactor);
        if (Number.isFinite(value) && displayByEmissions && obj[key] != null) {
          // in tCO2eq/min
          obj[key] *= d.exchangeCo2Intensities[key] / 1e3 / 60.0;
        }
      });
    }
    // Keep a pointer to original data
    obj._countryData = d;
    return obj;
  });

  // Prepare stack - order is defined here, from bottom to top
  const exchangeKeys = electricityMixMode === 'consumption' ? getExchangeKeys(historyData) : [];
  const stackKeys = modeOrder.concat(exchangeKeys);
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

const getMouseMoveHandler = () => (timeIndex) => {
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};
const getMouseOutHandler = () => () => {
  dispatchApplication('selectedZoneTimeIndex', null);
};
const getLayerMouseMoveHandler = (setSelectedLayerIndex, isMobile) => (timeIndex, layerIndex, layer, ev, svgRef) => {
  // If in mobile mode, put the tooltip to the top of the screen for
  // readability, otherwise float it depending on the cursor position.
  const tooltipPosition = !isMobile
    ? { x: ev.clientX - 7, y: svgRef.current.getBoundingClientRect().top - 7 }
    : { x: 0, y: 0 };
  setSelectedLayerIndex(layerIndex);
  dispatchApplication('tooltipPosition', tooltipPosition);
  dispatchApplication('tooltipZoneData', layer.data[timeIndex].data._countryData);
  dispatchApplication('tooltipDisplayMode', layer.key);
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};
const getLayerMouseOutHandler = setSelectedLayerIndex => () => {
  setSelectedLayerIndex(null);
  dispatchApplication('tooltipDisplayMode', null);
};

// Regular production mode fill or exchange fill as a fallback
const getFillSelector = (layers, displayByEmissions) => layerIndex => modeColor[layers[layerIndex].key]
  || (displayByEmissions ? 'darkgray' : `url(#country-history-mix-exchanges-${layers[layerIndex].key})`);

const getGradientStopColorSelector = co2ColorScale => (d, key) => (d._countryData.exchangeCo2Intensities
  ? co2ColorScale(d._countryData.exchangeCo2Intensities[key]) : 'darkgray');

const getCurrentTime = state =>
  state.application.customDate || (state.data.grid || {}).datetime;

const getSelectedZoneHistory = state =>
  state.data.histories[state.application.selectedZoneName];

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  currentTime: getCurrentTime(state),
  displayByEmissions: state.application.tableDisplayEmissions,
  electricityMixMode: state.application.electricityMixMode,
  historyData: getSelectedZoneHistory(state),
  isMobile: state.application.isMobile,
  selectedTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryHistoryMixGraph = ({
  colorBlindModeEnabled,
  currentTime,
  displayByEmissions,
  electricityMixMode,
  historyData,
  isMobile,
  selectedTimeIndex,
}) => {
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);

  // Graph state pre-processing (recalculated only when the graph data gets updated)
  const {
    datetimes,
    valueUnit,
    layers,
    exchangeLayers,
    maxTotalValue,
  } = useMemo(
    () => getGraphState(currentTime, historyData, displayByEmissions, electricityMixMode),
    [currentTime, historyData, displayByEmissions, electricityMixMode]
  );

  // Mouse action handlers
  const mouseMoveHandler = useMemo(getMouseMoveHandler, []);
  const mouseOutHandler = useMemo(getMouseOutHandler, []);
  const layerMouseMoveHandler = useMemo(
    () => getLayerMouseMoveHandler(setSelectedLayerIndex, isMobile),
    [setSelectedLayerIndex, isMobile]
  );
  const layerMouseOutHandler = useMemo(
    () => getLayerMouseOutHandler(setSelectedLayerIndex),
    [setSelectedLayerIndex]
  );

  // Labels and colors
  const valueAxisLabel = displayByEmissions ? 'tCO2eq/min' : valueUnit;
  const co2ColorScale = useMemo(
    () => getCo2Scale(colorBlindModeEnabled),
    [colorBlindModeEnabled]
  );
  const fillSelector = useMemo(
    () => getFillSelector(layers, displayByEmissions),
    [layers, displayByEmissions]
  );
  const gradientStopColorSelector = useMemo(
    () => getGradientStopColorSelector(co2ColorScale),
    [co2ColorScale]
  );

  if (!layers) return null;

  return (
    <AreaGraph
      layers={layers}
      gradientIdPrefix="country-history-mix-exchanges"
      gradientLayers={exchangeLayers}
      gradientStopColorSelector={gradientStopColorSelector}
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
      isMobile={isMobile}
    />
  );
};

export default connect(mapStateToProps)(CountryHistoryMixGraph);
