import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { useParams } from 'react-router-dom';

import { DATA_FETCH_INTERVAL, TIME } from '../helpers/constants';
import {
  GRID_DATA_FETCH_REQUESTED,
  SOLAR_DATA_FETCH_REQUESTED,
  WIND_DATA_FETCH_REQUESTED,
  ZONE_HISTORY_FETCH_REQUESTED,
} from '../helpers/redux';

import { useWindEnabled, useSolarEnabled, useFeatureToggle, ParamTypes } from './router';

export function useConditionalZoneHistoryFetch() {
  const { zoneId } = useParams<ParamTypes>();
  const zones = useSelector((state) => (state as any).data.zones);
  const features = useFeatureToggle();
  const selectedTimeAggregate = useSelector((state) => (state as any).application.selectedTimeAggregate);
  const dispatch = useDispatch();

  // Fetch zone history data only if it's not there yet (and custom timestamp is not used).
  useEffect(() => {
    const isExpired = zones[zoneId]?.[selectedTimeAggregate].isExpired;
    if (zoneId && isExpired) {
      // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
      dispatch(ZONE_HISTORY_FETCH_REQUESTED({ zoneId, features, selectedTimeAggregate }));
    }
  }, [zoneId, dispatch, features, selectedTimeAggregate, zones]);
}

export function useGridDataPolling() {
  const features = useFeatureToggle();
  const zones = useSelector((state) => (state as any).data.zones);
  const selectedTimeAggregate = useSelector((state) => (state as any).application.selectedTimeAggregate);
  const dispatch = useDispatch();

  const hasOverviewData = Object.keys(zones).some((zoneId) => zones[zoneId][selectedTimeAggregate].overviews.length);
  const isExpired = useSelector((state) => (state as any).data.isGridExpired[selectedTimeAggregate]);
  // After initial request, do the polling only if the custom datetime is not specified.
  useEffect(() => {
    if (!hasOverviewData || isExpired) {
      // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
      dispatch(GRID_DATA_FETCH_REQUESTED({ features, selectedTimeAggregate }));
    }

    const pollInterval = setInterval(() => {
      if (selectedTimeAggregate === TIME.HOURLY) {
        dispatch(
          // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
          GRID_DATA_FETCH_REQUESTED({
            features,
            // We only refetch hourly state as the other aggregates are not updated frequently enough to justify a refresh
            selectedTimeAggregate: TIME.HOURLY,
          })
        );
      }
    }, DATA_FETCH_INTERVAL);
    return () => clearInterval(pollInterval);
  }, [dispatch, features, selectedTimeAggregate, hasOverviewData, isExpired]);
}

export function useConditionalWindDataPolling() {
  // TODO: ensure Wind/Solar is able to refetch if newer data were to become available
  const windEnabled = useWindEnabled();
  const windData = useSelector((state) => (state as any).data.wind);
  const dispatch = useDispatch();

  useEffect(() => {
    let pollInterval: any;
    if (windEnabled && !windData) {
      dispatch(WIND_DATA_FETCH_REQUESTED());
      pollInterval = setInterval(() => {
        dispatch(WIND_DATA_FETCH_REQUESTED());
      }, DATA_FETCH_INTERVAL);
    }
    return () => clearInterval(pollInterval);
  }, [windEnabled, dispatch, windData]);
}

export function useConditionalSolarDataPolling() {
  // TODO: ensure Wind/Solar is able to refetch if newer data were to become available
  const solarEnabled = useSolarEnabled();
  const solarData = useSelector((state) => (state as any).data.solar);
  const dispatch = useDispatch();

  // After initial request, do the polling only if the custom datetime is not specified.
  useEffect(() => {
    let pollInterval: any;
    if (solarEnabled && !solarData) {
      dispatch(SOLAR_DATA_FETCH_REQUESTED());
      pollInterval = setInterval(() => {
        dispatch(SOLAR_DATA_FETCH_REQUESTED());
      }, DATA_FETCH_INTERVAL);
    }
    return () => clearInterval(pollInterval);
  }, [solarEnabled, dispatch, solarData]);
}
