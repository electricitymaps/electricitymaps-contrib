import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { isEmpty } from 'lodash';
import moment from 'moment';

import { useCustomDatetime, useWindEnabled, useSolarEnabled } from '../helpers/router';
import { DATA_FETCH_INTERVAL } from '../helpers/constants';

import { useCurrentZoneHistory } from './redux';

export function useClientVersionFetch() {
  const clientType = useSelector(state => state.application.clientType);
  const isLocalhost = useSelector(state => state.application.isLocalhost);
  const dispatch = useDispatch();

  // We only check the latest client version if running in browser on non-localhost.
  useEffect(() => {
    if (clientType === 'web' && !isLocalhost) {
      dispatch({ type: 'CLIENT_VERSION_FETCH_REQUESTED' });
    }
  }, [clientType, isLocalhost]);
}

export function useConditionalZoneHistoryFetch() {
  const { zoneId } = useParams();
  const historyData = useCurrentZoneHistory();
  const customDatetime = useCustomDatetime();
  const dispatch = useDispatch();

  // Fetch zone history data only if it's not there yet (and custom timestamp is not used).
  useEffect(() => {
    if (customDatetime) {
      console.error('Can\'t fetch history when a custom date is provided!');
    } else if (zoneId && isEmpty(historyData)) {
      dispatch({ type: 'ZONE_HISTORY_FETCH_REQUESTED', payload: { zoneId } });
    }
  }, [zoneId, historyData, customDatetime]);
}

export function useGridDataPolling() {
  const datetime = useCustomDatetime();
  const dispatch = useDispatch();

  let pollInterval;

  // After initial request, do the polling only if the custom datetime is not specified.
  useEffect(() => {
    clearInterval(pollInterval);
    dispatch({ type: 'GRID_DATA_FETCH_REQUESTED', payload: { datetime } });
    if (!datetime) {
      pollInterval = setInterval(() => {
        dispatch({ type: 'GRID_DATA_FETCH_REQUESTED', payload: { datetime } });
      }, DATA_FETCH_INTERVAL);
    }
  }, [datetime]);
}

export function useConditionalWindDataPolling() {
  const windEnabled = useWindEnabled();
  const customDatetime = useCustomDatetime();
  const datetime = moment(customDatetime || new Date());
  const dispatch = useDispatch();

  let pollInterval;

  // After initial request, do the polling only if the custom datetime is not specified.
  useEffect(() => {
    clearInterval(pollInterval);
    if (windEnabled) {
      dispatch({ type: 'WIND_DATA_FETCH_REQUESTED', payload: { datetime } });
      if (!customDatetime) {
        pollInterval = setInterval(() => {
          dispatch({ type: 'WIND_DATA_FETCH_REQUESTED', payload: { datetime } });
        }, DATA_FETCH_INTERVAL);
      }
    } else {
      // TODO: Find a nicer way to invalidate the wind data (or remove it altogether when wind layer is moved to React).
      dispatch({ type: 'WIND_DATA_FETCH_SUCCEEDED', payload: null });
    }
  }, [windEnabled, datetime]);
}

export function useConditionalSolarDataPolling() {
  const solarEnabled = useSolarEnabled();
  const customDatetime = useCustomDatetime();
  const datetime = moment(customDatetime || new Date());
  const dispatch = useDispatch();

  let pollInterval;

  // After initial request, do the polling only if the custom datetime is not specified.
  useEffect(() => {
    clearInterval(pollInterval);
    if (solarEnabled) {
      dispatch({ type: 'SOLAR_DATA_FETCH_REQUESTED', payload: { datetime } });
      if (!customDatetime) {
        pollInterval = setInterval(() => {
          dispatch({ type: 'SOLAR_DATA_FETCH_REQUESTED', payload: { datetime } });
        }, DATA_FETCH_INTERVAL);
      }
    } else {
      // TODO: Find a nicer way to invalidate the solar data (or remove it altogether when solar layer is moved to React).
      dispatch({ type: 'SOLAR_DATA_FETCH_SUCCEEDED', payload: null });
    }
  }, [solarEnabled, datetime]);
}
