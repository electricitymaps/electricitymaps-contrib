import moment from 'moment';
import {
  flatMap,
  keys,
  sortBy,
  uniq,
} from 'lodash';

export function getZoneHistory(zoneId) {
  return state => state.data.histories[zoneId] || [];
}

export function getZoneExchangeKeys(zoneId) {
  return state => (state.application.electricityMixMode === 'consumption'
    ? sortBy(uniq(flatMap(getZoneHistory(zoneId)(state), d => keys(d.exchange))))
    : []);
}

export function getZoneHistoryDatetimes(zoneId) {
  return state => getZoneHistory(zoneId)(state).map(d => moment(d.stateDatetime).toDate());
}

// Use current time as the end time of the graph time scale explicitly
// as we want to make sure we account for the missing data at the end of
// the graph (when not inferable from historyData timestamps).
export function getZoneHistoryEndTime(customDatetime) {
  return state => moment(customDatetime || (state.data.grid || {}).datetime).format();
}

// TODO: Likewise, we should be passing an explicit startTime set to 24h
// in the past to make sure we show data is missing at the beginning of
// the graph, but right now that would create UI inconsistency with the
// other neighbouring graphs showing data over a bit longer time scale
// (see https://github.com/tmrowco/electricitymap-contrib/issues/2250).
export function getZoneHistoryStartTime() {
  return state => null;
}

export function getZoneData(zoneId) {
  return (state) => {
    const zoneTimeIndex = state.application.selectedZoneTimeIndex;
    if (!state.data.grid || !zoneId) {
      return null;
    }
    if (zoneTimeIndex === null) {
      return state.data.grid.zones[zoneId];
    }
    return getZoneHistory(zoneId)(state)[zoneTimeIndex];
  };
}
