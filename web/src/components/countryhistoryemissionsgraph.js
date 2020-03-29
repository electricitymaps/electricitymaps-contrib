import moment from 'moment';
import React, { useMemo, useState } from 'react';
import { connect } from 'react-redux';
import { scaleLinear } from 'd3-scale';
import { max as d3Max } from 'd3-array';

import { EMISSIONS_GRAPH_LAYER_KEY } from '../helpers/constants';
import { getCo2Scale } from '../helpers/scales';
import {
  getSelectedZoneHistory,
  getZoneHistoryStartTime,
  getZoneHistoryEndTime,
} from '../selectors';
import {
  createSingleLayerGraphBackgroundMouseMoveHandler,
  createSingleLayerGraphBackgroundMouseOutHandler,
  createGraphLayerMouseMoveHandler,
  createGraphLayerMouseOutHandler,
} from '../helpers/history';
import { tonsPerHourToGramsPerMinute } from '../helpers/math';
import { getTotalElectricity } from '../helpers/zonedata';

import AreaGraph from './graph/areagraph';

const prepareGraphData = (historyData) => {
  if (!historyData || !historyData[0]) return {};

  const data = historyData.map(d => ({
    [EMISSIONS_GRAPH_LAYER_KEY]: tonsPerHourToGramsPerMinute(getTotalElectricity(d, true)),
    datetime: moment(d.stateDatetime).toDate(),
    // Keep a pointer to original data
    _countryData: d,
  }));

  const maxEmissions = d3Max(data.map(d => d[EMISSIONS_GRAPH_LAYER_KEY]));
  const emissionsColorScale = scaleLinear()
    .domain([0, maxEmissions])
    .range(['yellow', 'brown']);

  const layerKeys = [EMISSIONS_GRAPH_LAYER_KEY];
  const layerFill = key => d => emissionsColorScale(d.data[key]);
  return { data, layerKeys, layerFill };
};

const mapStateToProps = state => ({
  startTime: getZoneHistoryStartTime(state),
  endTime: getZoneHistoryEndTime(state),
  historyData: getSelectedZoneHistory(state),
  isMobile: state.application.isMobile,
  selectedTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryHistoryEmissionsGraph = ({
  displayByEmissions,
  startTime,
  endTime,
  historyData,
  isMobile,
  selectedTimeIndex,
}) => {
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill } = useMemo(
    () => prepareGraphData(historyData),
    [historyData]
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
      valueAxisLabel="tCO2eq / min"
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

export default connect(mapStateToProps)(CountryHistoryEmissionsGraph);
