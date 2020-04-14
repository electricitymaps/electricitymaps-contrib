import moment from 'moment';
import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import {
  flatMap,
  keys,
  sortBy,
  uniq,
} from 'lodash';

import { useCustomDatetime } from '../helpers/router';

export function useCurrentZoneHistory() {
  const { zoneId } = useParams();

  const selector = useMemo(
    () => state => state.data.histories[zoneId] || [],
    [zoneId],
  );

  return useSelector(selector);
}


export function useCurrentZoneHistoryDatetimes() {
  const zoneHistory = useCurrentZoneHistory();

  return useMemo(
    () => () => zoneHistory.map(d => moment(d.stateDatetime).toDate()),
    [zoneHistory],
  );
}

export function useCurrentZoneExchangeKeys() {
  const zoneHistory = useCurrentZoneHistory();

  const selector = useMemo(
    () => state => (
      state.application.electricityMixMode === 'consumption'
        ? sortBy(uniq(flatMap(zoneHistory, d => keys(d.exchange))))
        : []
    ),
    [zoneHistory]
  );

  return useSelector(selector);
}

// Use current time as the end time of the graph time scale explicitly
// as we want to make sure we account for the missing data at the end of
// the graph (when not inferable from historyData timestamps).
export function useCurrentZoneHistoryEndTime() {
  const customDatetime = useCustomDatetime();

  const selector = useMemo(
    () => state => (
      moment(customDatetime || (state.data.grid || {}).datetime).format()
    ),
    [customDatetime],
  );

  return useSelector(selector);
}

// TODO: Likewise, we should be passing an explicit startTime set to 24h
// in the past to make sure we show data is missing at the beginning of
// the graph, but right now that would create UI inconsistency with the
// other neighbouring graphs showing data over a bit longer time scale
// (see https://github.com/tmrowco/electricitymap-contrib/issues/2250).
export function useCurrentZoneHistoryStartTime() {
  const selector = useMemo(
    () => state => null,
    [],
  );
  return useSelector(selector);
}

export function useCurrentZoneData() {
  const { zoneId } = useParams();
  const zoneHistory = useCurrentZoneHistory();

  const selector = useMemo(
    () => (state) => {
      if (!state.data.grid || !zoneId) {
        return null;
      }
      const zoneTimeIndex = state.application.selectedZoneTimeIndex;
      if (zoneTimeIndex === null) {
        return state.data.grid.zones[zoneId];
      }
      return zoneHistory[zoneTimeIndex];
    },
    [zoneId, zoneHistory],
  );

  return useSelector(selector);
}
