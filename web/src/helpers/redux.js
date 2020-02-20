import {
  flatMap,
  keys,
  sortBy,
  uniq,
} from 'lodash';

export function getExchangeKeys(zoneHistory) {
  return sortBy(uniq(flatMap(zoneHistory, d => keys(d.exchange))));
}

export function getCurrentZoneData(state) {
  const { grid } = state.data;
  const zoneName = state.application.selectedZoneName;
  const i = state.application.selectedZoneTimeIndex;
  if (!grid || !zoneName) {
    return null;
  }
  if (i == null) {
    return grid.zones[zoneName];
  }
  return (state.data.histories[zoneName] || {})[i];
}
