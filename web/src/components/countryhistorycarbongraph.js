import moment from 'moment';
import React, { useMemo, useState } from 'react';
import { connect } from 'react-redux';

import { CARBON_GRAPH_LAYER_KEY } from '../helpers/constants';
import { getCo2Scale } from '../helpers/scales';
import {
  getSelectedZoneHistory,
  getZoneHistoryStartTime,
  getZoneHistoryEndTime,
  createSingleLayerGraphBackgroundMouseMoveHandler,
  createSingleLayerGraphBackgroundMouseOutHandler,
  createGraphLayerMouseMoveHandler,
  createGraphLayerMouseOutHandler,
} from '../helpers/history';

import AreaGraph from './graph/areagraph';

const prepareGraphData = (historyData, colorBlindModeEnabled, electricityMixMode) => {
  if (!historyData || !historyData[0]) return {};

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const data = historyData.map(d => ({
    [CARBON_GRAPH_LAYER_KEY]: electricityMixMode === 'consumption'
      ? d.co2intensity
      : d.co2intensityProduction,
    datetime: moment(d.stateDatetime).toDate(),
    // Keep a pointer to original data
    _countryData: d,
  }));
  const layerKeys = [CARBON_GRAPH_LAYER_KEY];
  const layerFill = key => d => co2ColorScale(d.data[key]);
  return { data, layerKeys, layerFill };
};

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  electricityMixMode: state.application.electricityMixMode,
  startTime: getZoneHistoryStartTime(state),
  endTime: getZoneHistoryEndTime(state),
  historyData: getSelectedZoneHistory(state),
  isMobile: state.application.isMobile,
  selectedTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryHistoryCarbonGraph = ({
  colorBlindModeEnabled,
  electricityMixMode,
  startTime,
  endTime,
  historyData,
  isMobile,
  selectedTimeIndex,
}) => {
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill } = useMemo(
    () => prepareGraphData(historyData, colorBlindModeEnabled, electricityMixMode),
    [historyData, colorBlindModeEnabled, electricityMixMode]
  );

  // Mouse action handlers
  const backgroundMouseMoveHandler = useMemo(
    () => createSingleLayerGraphBackgroundMouseMoveHandler(isMobile, setSelectedLayerIndex),
    [isMobile, setSelectedLayerIndex]
  );
  const backgroundMouseOutHandler = useMemo(
    () => createSingleLayerGraphBackgroundMouseOutHandler(setSelectedLayerIndex),
    [setSelectedLayerIndex]
  );
  const layerMouseMoveHandler = useMemo(
    () => createGraphLayerMouseMoveHandler(isMobile, setSelectedLayerIndex),
    [isMobile, setSelectedLayerIndex]
  );
  const layerMouseOutHandler = useMemo(
    () => createGraphLayerMouseOutHandler(setSelectedLayerIndex),
    [setSelectedLayerIndex]
  );

  return (
    <AreaGraph
      data={data}
      layerKeys={layerKeys}
      layerFill={layerFill}
      startTime={startTime}
      endTime={endTime}
      valueAxisLabel="g / kWh"
      backgroundMouseMoveHandler={backgroundMouseMoveHandler}
      backgroundMouseOutHandler={backgroundMouseOutHandler}
      layerMouseMoveHandler={layerMouseMoveHandler}
      layerMouseOutHandler={layerMouseOutHandler}
      selectedTimeIndex={selectedTimeIndex}
      selectedLayerIndex={selectedLayerIndex}
      isMobile={isMobile}
      height="8em"
    />
  );
};

export default connect(mapStateToProps)(CountryHistoryCarbonGraph);
