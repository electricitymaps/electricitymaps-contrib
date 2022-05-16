import { addDays, startOfDay, subDays } from 'date-fns';
import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { getSunrise, getSunset } from 'sunrise-sunset-js';

import { useCustomDatetime } from './router';

import { getCenteredZoneViewport } from '../helpers/map';

export function useCurrentZoneHistory() {
  const { zoneId } = useParams();
  const histories = useSelector((state) => state.data.histories);

  return useMemo(() => histories[zoneId] || null, [histories, zoneId]);
}

export function useCurrentDatetimes() {
  // TODO: should use V5 state here and v5 should tell the state datetimes
  const histories = useSelector((state) => state.data.histories);
  if (histories && Object.keys(histories).length) {
    return histories[Object.keys(histories)[0]].map((h) => new Date(h.stateDatetime));
  } else {
    return [];
  }
}

export function useCurrentZoneHistoryDatetimes() {
  const zoneHistory = useCurrentZoneHistory();

  return useMemo(() => (!zoneHistory ? [] : zoneHistory.map((d) => new Date(d.stateDatetime))), [zoneHistory]);
}

// Use current time as the end time of the graph time scale explicitly
// as we want to make sure we account for the missing data at the end of
// the graph (when not inferable from historyData timestamps).
export function useCurrentZoneHistoryEndTime() {
  const customDatetime = useCustomDatetime();
  const gridDatetime = useSelector((state) => (state.data.grid || {}).datetime);

  return useMemo(
    () => new Date(customDatetime || (gridDatetime ?? Date.now())), // Moment return a date when gridDatetime is undefined, this matches that behavior.
    [customDatetime, gridDatetime]
  );
}

// TODO: Likewise, we should be passing an explicit startTime set to 24h
// in the past to make sure we show data is missing at the beginning of
// the graph, but right now that would create UI inconsistency with the
// other neighbouring graphs showing data over a bit longer time scale
// (see https://github.com/tmrowco/electricitymap-contrib/issues/2250).
export function useCurrentZoneHistoryStartTime() {
  return null;
}

export function useCurrentZoneData() {
  const { zoneId } = useParams();
  const zoneHistory = useCurrentZoneHistory();
  const zoneTimeIndex = useSelector((state) => state.application.selectedZoneTimeIndex);
  const grid = useSelector((state) => state.data.grid);

  return useMemo(() => {
    if (!zoneId || !grid || !zoneHistory) {
      return null;
    } else if (zoneTimeIndex === null) {
      // If null, return the latest history
      return zoneHistory.at(-1);
    } else {
      return zoneHistory[zoneTimeIndex];
    }
  }, [zoneId, zoneHistory, zoneTimeIndex, grid]);
}

export function useCurrentZoneExchangeKeys() {
  // Use the whole history (which doesn't depend on timestamp)
  // and fallback on current zone data
  const zoneHistory = useCurrentZoneHistory();
  const currentZoneData = useCurrentZoneData();
  const isConsumption = useSelector((state) => state.application.electricityMixMode === 'consumption');

  return useMemo(() => {
    if (!isConsumption || !zoneHistory) {
      return [];
    }
    const exchangeKeys = new Set();
    const zoneHistoryOrCurrent = zoneHistory || [currentZoneData];
    zoneHistoryOrCurrent.forEach((zoneData) => {
      if (zoneData.exchange) {
        Object.keys(zoneData.exchange).forEach((k) => exchangeKeys.add(k));
      }
    });
    return Array.from(exchangeKeys).sort();
  }, [isConsumption, zoneHistory, currentZoneData]);
}

export function useLoadingOverlayVisible() {
  const mapInitializing = useSelector((state) => state.application.isLoadingMap);
  const gridInitializing = useSelector((state) => state.data.isLoadingGrid && !state.data.hasInitializedGrid);
  const solarInitializing = useSelector((state) => state.data.isLoadingSolar && !state.data.solar);
  const windInitializing = useSelector((state) => state.data.isLoadingWind && !state.data.wind);
  return mapInitializing || gridInitializing || solarInitializing || windInitializing;
}

export function useSmallLoaderVisible() {
  const gridLoading = useSelector((state) => state.data.isLoadingGrid);
  const solarLoading = useSelector((state) => state.data.isLoadingSolar);
  const windLoading = useSelector((state) => state.data.isLoadingWind);
  return gridLoading || solarLoading || windLoading;
}

export function useCurrentNightTimes() {
  const { zoneId } = useParams();
  const zone = useSelector((state) => state.data.grid.zones[zoneId]);

  const datetimeStr = useSelector((state) => state.data.grid.datetime);
  const history = useCurrentZoneHistory();

  return useMemo(() => {
    if (!zone || !datetimeStr || !history || !history[0]) {
      return [];
    }
    const { latitude, longitude } = getCenteredZoneViewport(zone);
    const nightTimes = [];
    let baseDatetime = startOfDay(new Date(datetimeStr));

    const earliest = history && history[0] && new Date(history[0].stateDatetime);
    const latest = new Date(
      history && history[history.length - 1] ? history[history.length - 1].stateDatetime : datetimeStr
    );
    do {
      // Get last nightTime
      const nightStart = getSunset(latitude, longitude, baseDatetime);
      let nightEnd = getSunrise(latitude, longitude, baseDatetime);
      // Due to some bug in the library, sometimes we get nightStart > nightEnd
      if (nightStart.getTime() > nightEnd.getTime()) {
        nightEnd = addDays(nightEnd, 1);
      }
      // Only use nights that start before the latest time we have
      // and that finishes after the earliest time we have
      if (nightStart.getTime() < latest.getTime() && nightEnd.getTime() > earliest.getTime()) {
        nightTimes.push([nightStart, nightEnd]);
      }

      // Abort at the first night that starts before our earliest time
      if (nightStart.getTime() < earliest.getTime()) {
        return nightTimes;
      }

      // Iterate to previous day
      baseDatetime = subDays(baseDatetime, 1);
      // The looping logic is handled inside the "do" block
      // eslint-disable-next-line no-constant-condition
    } while (true);
  }, [zone, datetimeStr, history]);
}
