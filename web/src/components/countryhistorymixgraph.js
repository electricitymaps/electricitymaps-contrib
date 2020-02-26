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

const getValuesInfo = (historyData, displayByEmissions) => {
  const maxTotalValue = d3Max(historyData, d => (
    displayByEmissions
      ? (d.totalCo2Production + d.totalCo2Import + d.totalCo2Discharge) / 1e6 / 60.0 // in tCO2eq/min
      : (d.totalProduction + d.totalImport + d.totalDischarge) // in MW
  ));
  const format = formatting.scalePower(maxTotalValue);

  const valueAxisLabel = displayByEmissions ? 'tCO2eq/min' : format.unit;
  const valueFactor = format.formattingFactor;
  return { valueAxisLabel, valueFactor };
};

const prepareGraphData = (historyData, colorBlindModeEnabled, displayByEmissions, electricityMixMode) => {
  if (!historyData || !historyData[0]) return {};

  const { valueAxisLabel, valueFactor } = getValuesInfo(historyData, displayByEmissions);
  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);

  // Format history data received by the API
  // TODO: Simplify this function and make it more readable
  const data = historyData.map((d) => {
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

  // If in consumption mode, show the exchange layers on top of the standard sources.
  let layerKeys = modeOrder;
  if (electricityMixMode === 'consumption') {
    layerKeys = layerKeys.concat(getExchangeKeys(historyData));
  }

  const layerFill = (key) => {
    // If exchange layer, set the horizontal gradient by using a different fill for each datapoint.
    if (getExchangeKeys(historyData).includes(key)) {
      return d => (d.data._countryData.exchangeCo2Intensities
        ? co2ColorScale(d.data._countryData.exchangeCo2Intensities[key]) : 'darkgray');
    }
    // Otherwise use regular production fill.
    return modeColor[key];
  };

  return {
    data,
    layerKeys,
    layerFill,
    valueAxisLabel,
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
  dispatchApplication('tooltipZoneData', layer.datapoints[timeIndex].data._countryData);
  dispatchApplication('tooltipDisplayMode', layer.key);
  dispatchApplication('selectedZoneTimeIndex', timeIndex);
};
const getLayerMouseOutHandler = setSelectedLayerIndex => () => {
  setSelectedLayerIndex(null);
  dispatchApplication('tooltipDisplayMode', null);
};

const getCurrentTime = state =>
  state.application.customDate || (state.data.grid || {}).datetime;

const getSelectedZoneHistory = state =>
  state.data.histories[state.application.selectedZoneName];

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  displayByEmissions: state.application.tableDisplayEmissions,
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

const CountryHistoryMixGraph = ({
  colorBlindModeEnabled,
  displayByEmissions,
  electricityMixMode,
  endTime,
  historyData,
  isMobile,
  selectedTimeIndex,
}) => {
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);

  // Recalculate graph data only when the history data is changed
  const {
    data,
    layerKeys,
    layerFill,
    valueAxisLabel,
  } = useMemo(
    () => prepareGraphData(historyData, colorBlindModeEnabled, displayByEmissions, electricityMixMode),
    [historyData, colorBlindModeEnabled, displayByEmissions, electricityMixMode]
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

  return (
    <AreaGraph
      data={data}
      layerKeys={layerKeys}
      layerFill={layerFill}
      endTime={endTime}
      valueAxisLabel={valueAxisLabel}
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
