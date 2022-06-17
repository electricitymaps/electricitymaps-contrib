import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';

import { DATA_FETCH_INTERVAL } from '../helpers/constants';

import { useCustomDatetime, useWindEnabled, useSolarEnabled, useFeatureToggle } from './router';

export function useConditionalZoneHistoryFetch() {
  const { zoneId } = useParams();
  const zones = useSelector((state) => state.data.zones);
  const customDatetime = useCustomDatetime();
  const features = useFeatureToggle();
  const selectedTimeAggregate = useSelector((state) => state.application.selectedTimeAggregate);
  const dispatch = useDispatch();

  // Fetch zone history data only if it's not there yet (and custom timestamp is not used).
  useEffect(() => {
    if (customDatetime) {
      console.error("Can't fetch history when a custom date is provided!");
    }

    const hasDetailedHistory = zones[zoneId]?.[selectedTimeAggregate].details.length;
    if (zoneId && !hasDetailedHistory) {
      dispatch({ type: 'ZONE_HISTORY_FETCH_REQUESTED', payload: { zoneId, features, selectedTimeAggregate } });
    }
  }, [zoneId, customDatetime, dispatch, features, selectedTimeAggregate, zones]);
}

export function useGridDataPolling() {
  const datetime = useCustomDatetime();
  const features = useFeatureToggle();
  const zones = useSelector((state) => state.data.zones);
  const selectedTimeAggregate = useSelector((state) => state.application.selectedTimeAggregate);
  const dispatch = useDispatch();

  const hasOverviewData = Object.keys(zones).some((zoneId) => zones[zoneId][selectedTimeAggregate].overviews.length);
  // After initial request, do the polling only if the custom datetime is not specified.
  useEffect(() => {
    let pollInterval;
    if (!hasOverviewData) {
      dispatch({ type: 'GRID_DATA_FETCH_REQUESTED', payload: { datetime, features, selectedTimeAggregate } });
    }
    if (!datetime) {
      pollInterval = setInterval(() => {
        dispatch({ type: 'GRID_DATA_FETCH_REQUESTED', payload: { datetime, features, selectedTimeAggregate } });
      }, DATA_FETCH_INTERVAL);
    }
    return () => clearInterval(pollInterval);
  }, [datetime, dispatch, features, selectedTimeAggregate, hasOverviewData]);
}

export function useConditionalWindDataPolling() {
  const windEnabled = useWindEnabled();
  const customDatetime = useCustomDatetime();
  const dispatch = useDispatch();

  // After initial request, do the polling only if the custom datetime is not specified.
  useEffect(() => {
    let pollInterval;
    if (windEnabled) {
      if (customDatetime) {
        dispatch({ type: 'WIND_DATA_FETCH_REQUESTED', payload: { datetime: customDatetime } });
      } else {
        dispatch({ type: 'WIND_DATA_FETCH_REQUESTED' });
        pollInterval = setInterval(() => {
          dispatch({ type: 'WIND_DATA_FETCH_REQUESTED' });
        }, DATA_FETCH_INTERVAL);
      }
    } else {
      // TODO: Find a nicer way to invalidate the wind data (or remove it altogether when wind layer is moved to React).
      dispatch({ type: 'WIND_DATA_FETCH_SUCCEEDED', payload: null });
    }
    return () => clearInterval(pollInterval);
  }, [windEnabled, customDatetime, dispatch]);
}

export function useConditionalSolarDataPolling() {
  const solarEnabled = useSolarEnabled();
  const customDatetime = useCustomDatetime();
  const dispatch = useDispatch();

  // After initial request, do the polling only if the custom datetime is not specified.
  useEffect(() => {
    let pollInterval;
    if (solarEnabled) {
      if (customDatetime) {
        dispatch({ type: 'SOLAR_DATA_FETCH_REQUESTED', payload: { datetime: customDatetime } });
      } else {
        dispatch({ type: 'SOLAR_DATA_FETCH_REQUESTED' });
        pollInterval = setInterval(() => {
          dispatch({ type: 'SOLAR_DATA_FETCH_REQUESTED' });
        }, DATA_FETCH_INTERVAL);
      }
    } else {
      // TODO: Find a nicer way to invalidate the solar data (or remove it altogether when solar layer is moved to React).
      dispatch({ type: 'SOLAR_DATA_FETCH_SUCCEEDED', payload: null });
    }
    return () => clearInterval(pollInterval);
  }, [solarEnabled, customDatetime, dispatch]);
}
