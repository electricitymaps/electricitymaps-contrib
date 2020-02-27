import moment from 'moment';
import React, { useState, useMemo, useCallback } from 'react';
import getSymbolFromCurrency from 'currency-symbol-map';
import { max as d3Max } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { connect } from 'react-redux';
import { forEach, first } from 'lodash';

import { dispatchApplication } from '../store';
import formatting from '../helpers/formatting';
import {
  createGraphMouseMoveHandler,
  createGraphMouseOutHandler,
  createGraphLayerMouseMoveHandler,
  createGraphLayerMouseOutHandler,
} from '../helpers/history';

import AreaGraph from './graph/areagraph';

const prepareGraphData = (historyData, colorBlindModeEnabled, electricityMixMode) => {
  if (!historyData || !historyData[0]) return {};

  const currencySymbol = getSymbolFromCurrency(((first(historyData) || {}).price || {}).currency);
  const valueAxisLabel = `${currencySymbol || '?'} / MWh`;

  const priceColorScale = scaleLinear()
    .domain([0, d3Max(historyData.map(d => (d.price || {}).value))])
    .range(['yellow', 'red']);
  const data = historyData.map(d => ({
    price: d.price && d.price.value,
    datetime: moment(d.stateDatetime).toDate(),
    // Keep a pointer to original data
    _countryData: d,
  }));
  const layerKeys = ['price'];
  const layerStroke = () => 'darkgray';
  const layerFill = () => '#616161';
  const focusFill = () => d => priceColorScale(d.data.price);
  return {
    data,
    layerKeys,
    layerStroke,
    layerFill,
    focusFill,
    valueAxisLabel,
  };
};

const getCurrentTime = state =>
  state.application.customDate || (state.data.grid || {}).datetime;

const getSelectedZoneHistory = state =>
  state.data.histories[state.application.selectedZoneName];

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  electricityMixMode: state.application.electricityMixMode,
  // Pass current time as the end time of the graph time scale explicitly
  // as we want to make sure we account for the missing data at the end of
  // the graph (when not inferable from historyData timestamps).
  // TODO: Likewise, we should be passing an explicit startTime set to 24h
  // in the past to make sure we show data is missing at the beginning of
  // the graph, but that would create UI inconsistency with the other
  // neighbouring graphs showing data over a bit longer time scale
  // (see https://github.com/tmrowco/electricitymap-contrib/issues/2250).
  endTime: moment(getCurrentTime(state)).format(),
  historyData: getSelectedZoneHistory(state),
  isMobile: state.application.isMobile,
  selectedTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryHistoryPricesGraph = ({
  colorBlindModeEnabled,
  electricityMixMode,
  endTime,
  historyData,
  isMobile,
  selectedTimeIndex,
}) => {
  // Recalculate graph data only when the history data is changed
  const {
    data,
    layerKeys,
    layerStroke,
    layerFill,
    focusFill,
    valueAxisLabel,
  } = useMemo(
    () => prepareGraphData(historyData, colorBlindModeEnabled, electricityMixMode),
    [historyData, colorBlindModeEnabled, electricityMixMode]
  );

  // Mouse action handlers
  const mouseMoveHandler = useMemo(createGraphMouseMoveHandler, []);
  const mouseOutHandler = useMemo(createGraphMouseOutHandler, []);
  const layerMouseMoveHandler = useMemo(() => createGraphLayerMouseMoveHandler(isMobile), [isMobile]);
  const layerMouseOutHandler = useMemo(createGraphLayerMouseOutHandler, []);

  return (
    <AreaGraph
      data={data}
      layerKeys={layerKeys}
      layerStroke={layerStroke}
      layerFill={layerFill}
      focusFill={focusFill}
      endTime={endTime}
      valueAxisLabel={valueAxisLabel}
      mouseMoveHandler={mouseMoveHandler}
      mouseOutHandler={mouseOutHandler}
      layerMouseMoveHandler={layerMouseMoveHandler}
      layerMouseOutHandler={layerMouseOutHandler}
      selectedTimeIndex={selectedTimeIndex}
      selectedLayerIndex={0}
      isMobile={isMobile}
      height="6em"
    />
  );
};

export default connect(mapStateToProps)(CountryHistoryPricesGraph);
