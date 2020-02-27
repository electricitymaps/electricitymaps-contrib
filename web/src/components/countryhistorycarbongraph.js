import moment from 'moment';
import React, { useState, useMemo, useCallback } from 'react';
import { max as d3Max } from 'd3-array';
import { connect } from 'react-redux';
import { forEach } from 'lodash';

import formatting from '../helpers/formatting';
import { getCo2Scale } from '../helpers/scales';
import { modeOrder, modeColor } from '../helpers/constants';
import { getExchangeKeys } from '../helpers/zones';
import { dispatchApplication } from '../store';

import AreaGraph from './graph/areagraph';

const prepareGraphData = (historyData, colorBlindModeEnabled, electricityMixMode) => {
  if (!historyData || !historyData[0]) return {};

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const data = historyData.map(d => ({
    carbon: electricityMixMode === 'consumption'
      ? d.co2intensity
      : d.co2intensityProduction,
    datetime: moment(d.stateDatetime).toDate(),
    // Keep a pointer to original data
    _countryData: d,
  }));
  const layerKeys = ['carbon'];
  const layerFill = () => d => co2ColorScale(d.data.carbon);
  return { data, layerKeys, layerFill };
};

const getMouseMoveHandler = () => (timeIndex) => {
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};
const getMouseOutHandler = () => () => {
  dispatchApplication('selectedZoneTimeIndex', null);
};
const getLayerMouseMoveHandler = isMobile => (timeIndex, layerIndex, layer, ev, svgRef) => {
  // If in mobile mode, put the tooltip to the top of the screen for
  // readability, otherwise float it depending on the cursor position.
  const tooltipPosition = !isMobile
    ? { x: ev.clientX - 7, y: svgRef.current.getBoundingClientRect().top - 7 }
    : { x: 0, y: 0 };
  dispatchApplication('tooltipPosition', tooltipPosition);
  dispatchApplication('tooltipZoneData', layer.datapoints[timeIndex].data._countryData);
  dispatchApplication('tooltipDisplayMode', layer.key);
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};
const getLayerMouseOutHandler = () => () => {
  dispatchApplication('tooltipDisplayMode', null);
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

const CountryHistoryCarbonGraph = ({
  colorBlindModeEnabled,
  electricityMixMode,
  endTime,
  historyData,
  isMobile,
  selectedTimeIndex,
}) => {
  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill } = useMemo(
    () => prepareGraphData(historyData, colorBlindModeEnabled, electricityMixMode),
    [historyData, colorBlindModeEnabled, electricityMixMode]
  );

  // Mouse action handlers
  const mouseMoveHandler = useMemo(getMouseMoveHandler, []);
  const mouseOutHandler = useMemo(getMouseOutHandler, []);
  const layerMouseMoveHandler = useMemo(() => getLayerMouseMoveHandler(isMobile), [isMobile]);
  const layerMouseOutHandler = useMemo(getLayerMouseOutHandler, []);

  return (
    <AreaGraph
      data={data}
      layerKeys={layerKeys}
      layerFill={layerFill}
      endTime={endTime}
      valueAxisLabel="g / kWh"
      mouseMoveHandler={mouseMoveHandler}
      mouseOutHandler={mouseOutHandler}
      layerMouseMoveHandler={layerMouseMoveHandler}
      layerMouseOutHandler={layerMouseOutHandler}
      selectedTimeIndex={selectedTimeIndex}
      selectedLayerIndex={0}
      isMobile={isMobile}
    />
  );
};

export default connect(mapStateToProps)(CountryHistoryCarbonGraph);
