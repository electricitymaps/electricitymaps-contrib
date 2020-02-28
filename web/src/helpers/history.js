import moment from 'moment';
import {
  flatMap,
  keys,
  sortBy,
  uniq,
} from 'lodash';

import { dispatchApplication } from '../store';

export function getExchangeKeys(zoneHistory) {
  return sortBy(uniq(flatMap(zoneHistory, d => keys(d.exchange))));
}

export function getSelectedZoneHistory(state) {
  return state.data.histories[state.application.selectedZoneName];
}

// Use current time as the end time of the graph time scale explicitly
// as we want to make sure we account for the missing data at the end of
// the graph (when not inferable from historyData timestamps).
export function getZoneHistoryGraphEndTime(state) {
  return moment(state.application.customDate || (state.data.grid || {}).datetime).format();
}

// TODO: Likewise, we should be passing an explicit startTime set to 24h
// in the past to make sure we show data is missing at the beginning of
// the graph, but right now that would create UI inconsistency with the
// other neighbouring graphs showing data over a bit longer time scale
// (see https://github.com/tmrowco/electricitymap-contrib/issues/2250).
export function getZoneHistoryGraphStartTime(state) {
  return null;
}

export function createGraphBackgroundMouseMoveHandler() {
  return (timeIndex) => {
    dispatchApplication('selectedZoneTimeIndex', timeIndex);
  };
}

export function createGraphBackgroundMouseOutHandler() {
  return () => {
    dispatchApplication('selectedZoneTimeIndex', null);
  };
}

export function createGraphLayerMouseMoveHandler(isMobile, setSelectedLayerIndex) {
  return (timeIndex, layerIndex, layer, ev, svgRef) => {
    // If in mobile mode, put the tooltip to the top of the screen for
    // readability, otherwise float it depending on the cursor position.
    const tooltipPosition = !isMobile
      ? { x: ev.clientX - 7, y: svgRef.current.getBoundingClientRect().top - 7 }
      : { x: 0, y: 0 };
    if (setSelectedLayerIndex) {
      setSelectedLayerIndex(layerIndex);
    }
    if (layer.datapoints[timeIndex]) {
      dispatchApplication('tooltipPosition', tooltipPosition);
      dispatchApplication('tooltipZoneData', layer.datapoints[timeIndex].data._countryData);
      dispatchApplication('tooltipDisplayMode', layer.key);
    }
    dispatchApplication('selectedZoneTimeIndex', timeIndex);
  };
}

export function createGraphLayerMouseOutHandler(setSelectedLayerIndex) {
  return () => {
    if (setSelectedLayerIndex) {
      setSelectedLayerIndex(null);
    }
    dispatchApplication('tooltipDisplayMode', null);
    dispatchApplication('selectedZoneTimeIndex', null);
  };
}
