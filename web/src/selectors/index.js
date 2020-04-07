import moment from 'moment';
import {
  flatMap,
  keys,
  sortBy,
  uniq,
} from 'lodash';
import { getCustomDatetime } from '../helpers/router';

export function getSelectedZoneHistory(state) {
  return state.data.histories[state.application.selectedZoneName] || [];
}

export function getSelectedZoneExchangeKeys(state) {
  return state.application.electricityMixMode === 'consumption'
    ? sortBy(uniq(flatMap(getSelectedZoneHistory(state), d => keys(d.exchange))))
    : [];
}

export function getSelectedZoneHistoryDatetimes(state) {
  return getSelectedZoneHistory(state).map(d => moment(d.stateDatetime).toDate());
}

// Use current time as the end time of the graph time scale explicitly
// as we want to make sure we account for the missing data at the end of
// the graph (when not inferable from historyData timestamps).
export function getZoneHistoryEndTime(state) {
  return moment(getCustomDatetime() || (state.data.grid || {}).datetime).format();
}

// TODO: Likewise, we should be passing an explicit startTime set to 24h
// in the past to make sure we show data is missing at the beginning of
// the graph, but right now that would create UI inconsistency with the
// other neighbouring graphs showing data over a bit longer time scale
// (see https://github.com/tmrowco/electricitymap-contrib/issues/2250).
export function getZoneHistoryStartTime(state) {
  return null;
}

export function getCurrentZoneData(state) {
  const zoneName = state.application.selectedZoneName;
  const zoneTimeIndex = state.application.selectedZoneTimeIndex;
  if (!state.data.grid || !zoneName) {
    return null;
  }
  if (zoneTimeIndex === null) {
    return state.data.grid.zones[zoneName];
  }
  return getSelectedZoneHistory(state)[zoneTimeIndex];
}
