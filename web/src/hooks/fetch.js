import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { isEmpty } from 'lodash';

import { useCustomDatetime } from '../helpers/router';
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
    dispatch({ type: 'GRID_DATA_FETCH_REQUESTED', payload: { datetime, showLoading: true } });
    if (!datetime) {
      pollInterval = setInterval(() => {
        dispatch({ type: 'GRID_DATA_FETCH_REQUESTED', payload: { showLoading: false } });
      }, DATA_FETCH_INTERVAL);
    }
  }, [datetime]);
}
