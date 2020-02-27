import {
  flatMap,
  keys,
  sortBy,
  uniq,
} from 'lodash';

export function getExchangeKeys(zoneHistory) {
  return sortBy(uniq(flatMap(zoneHistory, d => keys(d.exchange))));
}
