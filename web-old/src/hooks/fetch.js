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

import { useWindEnabled, useSolarEnabled, useFeatureToggle } from './router';

export function useConditionalZoneHistoryFetch() {
  const { zoneId } = useParams();
  const zones = useSelector((state) => state.data.zones);
  const features = useFeatureToggle();
  const selectedTimeAggregate = useSelector((state) => state.application.selectedTimeAggregate);
  const dispatch = useDispatch();

  // Fetch zone history data only if it's not there yet (and custom timestamp is not used).
  useEffect(() => {
    const isExpired = zones[zoneId]?.[selectedTimeAggregate].isExpired;
    if (zoneId && isExpired) {
      dispatch(ZONE_HISTORY_FETCH_REQUESTED({ zoneId, features, selectedTimeAggregate }));
    }
  }, [zoneId, dispatch, features, selectedTimeAggregate, zones]);
}

export function useGridDataPolling() {
  const features = useFeatureToggle();
  const zones = useSelector((state) => state.data.zones);
  const selectedTimeAggregate = useSelector((state) => state.application.selectedTimeAggregate);
  const dispatch = useDispatch();

  const hasOverviewData = Object.keys(zones).some((zoneId) => zones[zoneId][selectedTimeAggregate].overviews.length);
  const isExpired = useSelector((state) => state.data.isGridExpired[selectedTimeAggregate]);
  // After initial request, do the polling only if the custom datetime is not specified.
  useEffect(() => {
    if (!hasOverviewData || isExpired) {
      dispatch(GRID_DATA_FETCH_REQUESTED({ features, selectedTimeAggregate }));
    }

    const pollInterval = setInterval(() => {
      if (selectedTimeAggregate === TIME.HOURLY) {
        dispatch(
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
  const windData = useSelector((state) => state.data.wind);
  const dispatch = useDispatch();

  useEffect(() => {
    let pollInterval;
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
  const solarData = useSelector((state) => state.data.solar);
  const dispatch = useDispatch();

  // After initial request, do the polling only if the custom datetime is not specified.
  useEffect(() => {
    let pollInterval;
    if (solarEnabled && !solarData) {
      dispatch(SOLAR_DATA_FETCH_REQUESTED());
      pollInterval = setInterval(() => {
        dispatch(SOLAR_DATA_FETCH_REQUESTED());
      }, DATA_FETCH_INTERVAL);
    }
    return () => clearInterval(pollInterval);
  }, [solarEnabled, dispatch, solarData]);
}
