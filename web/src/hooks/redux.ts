import { useMemo } from 'react';
import { useSelector } from 'react-redux';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'reac... Remove this comment to see the full error message
import { useParams } from 'react-router-dom';

import { combineZoneData } from '../helpers/redux';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'loda... Remove this comment to see the full error message
import { mapValues } from 'lodash';

export function useCurrentZoneHistory() {
  const { zoneId } = useParams();
  const selectedTimeAggregate = useSelector((state) => (state as any).application.selectedTimeAggregate);
  const zones = useSelector((state) => (state as any).data.zones);
  return useMemo(() => {
    if (zones[zoneId]) {
      return combineZoneData(zones[zoneId], selectedTimeAggregate);
    }
    return [];
  }, [zoneId, zones, selectedTimeAggregate]);
}

export function useCurrentZoneList() {
  // returns dictionary of zones and combined data for the selected time aggregate
  const zones = useSelector((state) => (state as any).data.zones);
  const selectedTimeAggregate = useSelector((state) => (state as any).application.selectedTimeAggregate);
  const selectedZoneTimeIndex = useSelector((state) => (state as any).application.selectedZoneTimeIndex);
  if (!selectedZoneTimeIndex && selectedZoneTimeIndex !== 0) {
    return {};
  }
  const zoneList = mapValues(
    zones,
    (zone: any) => combineZoneData(zone, selectedTimeAggregate)[selectedZoneTimeIndex] || {}
  );

  return zoneList;
}

export function useCurrentDatetimes() {
  const selectedTimeAggregate = useSelector((state) => (state as any).application.selectedTimeAggregate);
  const datetimes = useSelector((state) => (state as any).data.zoneDatetimes[selectedTimeAggregate]);
  return datetimes || [];
}

// TODO: Should be replaced with useCurrentDatetimes
export function useCurrentZoneHistoryDatetimes() {
  const zoneHistory = useCurrentZoneHistory();

  return useMemo(() => (!zoneHistory ? [] : zoneHistory.map((d: any) => new Date(d.stateDatetime))), [zoneHistory]);
}

// Use current time as the end time of the graph time scale explicitly
// as we want to make sure we account for the missing data at the end of
// the graph (when not inferable from historyData timestamps).
// TODO: Can be deprecated when we switch to historical-view
export function useCurrentZoneHistoryEndTime() {
  const gridDatetime = useSelector((state) => ((state as any).data.grid || {}).datetime);

  return useMemo(
    () => new Date(gridDatetime ?? Date.now()), // Moment return a date when gridDatetime is undefined, this matches that behavior.
    [gridDatetime]
  );
}

// TODO: Likewise, we should be passing an explicit startTime set to 24h
// in the past to make sure we show data is missing at the beginning of
// the graph, but right now that would create UI inconsistency with the
// other neighbouring graphs showing data over a bit longer time scale
// (see https://github.com/tmrowco/electricitymap-contrib/issues/2250).
// TODO: Can be deprecated when we switch to historical-view
export function useCurrentZoneHistoryStartTime() {
  return null;
}

export function useCurrentZoneData() {
  const { zoneId } = useParams();
  const zoneHistory = useCurrentZoneHistory();
  const zoneTimeIndex = useSelector((state) => (state as any).application.selectedZoneTimeIndex);
  const zones = useSelector((state) => (state as any).data.zones);

  return useMemo(() => {
    if (!zoneId || !zones || !zoneHistory) {
      return null;
    } else if (zoneTimeIndex === null || zoneHistory.length === 1) {
      // if zonetimeIndex is null return latest history.
      // if there is only one element return that element
      return zoneHistory.at(-1);
    } else {
      return zoneHistory[zoneTimeIndex];
    }
  }, [zoneId, zoneHistory, zoneTimeIndex, zones]);
}

export function useCurrentZoneExchangeKeys() {
  // Use the whole history (which doesn't depend on timestamp)
  // and fallback on current zone data
  const zoneHistory = useCurrentZoneHistory();
  const currentZoneData = useCurrentZoneData();
  const isConsumption = useSelector((state) => (state as any).application.electricityMixMode === 'consumption');

  return useMemo(() => {
    if (!isConsumption || !zoneHistory) {
      return [];
    }
    const exchangeKeys = new Set();
    const zoneHistoryOrCurrent = zoneHistory || [currentZoneData];
    zoneHistoryOrCurrent.forEach((zoneData: any) => {
      if (zoneData.exchange) {
        Object.keys(zoneData.exchange).forEach((k) => exchangeKeys.add(k));
      }
    });
    return Array.from(exchangeKeys).sort();
  }, [isConsumption, zoneHistory, currentZoneData]);
}

export function useLoadingOverlayVisible() {
  const mapInitializing = useSelector((state) => (state as any).application.isLoadingMap);
  const gridInitializing = useSelector(
    (state) => (state as any).data.isLoadingGrid && !(state as any).data.hasInitializedGrid
  );
  const solarInitializing = useSelector((state) => (state as any).data.isLoadingSolar && !(state as any).data.solar);
  const windInitializing = useSelector((state) => (state as any).data.isLoadingWind && !(state as any).data.wind);
  return mapInitializing || gridInitializing || solarInitializing || windInitializing;
}
