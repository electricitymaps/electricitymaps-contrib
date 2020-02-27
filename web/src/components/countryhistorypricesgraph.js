import moment from 'moment';
import React, { useMemo } from 'react';
import getSymbolFromCurrency from 'currency-symbol-map';
import { max as d3Max } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { connect } from 'react-redux';
import { first } from 'lodash';

import { PRICES_GRAPH_LAYER_KEY } from '../helpers/constants';
import {
  getSelectedZoneHistory,
  getZoneHistoryGraphStartTime,
  getZoneHistoryGraphEndTime,
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

  const priceMaxValue = d3Max(historyData.map(d => (d.price || {}).value));
  const priceColorScale = scaleLinear()
    .domain([0, priceMaxValue])
    .range(['yellow', 'red']);

  const data = historyData.map(d => ({
    [PRICES_GRAPH_LAYER_KEY]: d.price && d.price.value,
    datetime: moment(d.stateDatetime).toDate(),
    // Keep a pointer to original data
    _countryData: d,
  }));

  const layerKeys = [PRICES_GRAPH_LAYER_KEY];
  const layerStroke = () => 'darkgray';
  const layerFill = () => '#616161';
  const focusFill = key => d => priceColorScale(d.data[key]);

  return {
    data,
    layerKeys,
    layerStroke,
    layerFill,
    focusFill,
    valueAxisLabel,
  };
};

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  electricityMixMode: state.application.electricityMixMode,
  startTime: getZoneHistoryGraphStartTime(state),
  endTime: getZoneHistoryGraphEndTime(state),
  historyData: getSelectedZoneHistory(state),
  isMobile: state.application.isMobile,
  selectedTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryHistoryPricesGraph = ({
  colorBlindModeEnabled,
  electricityMixMode,
  startTime,
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
      startTime={startTime}
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
