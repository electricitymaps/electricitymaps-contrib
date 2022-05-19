import { call, put, takeLatest } from 'redux-saga/effects';

import thirdPartyServices from '../services/thirdparty';
import { handleRequestError, protectedJsonRequest } from '../helpers/api';
import { getGfsTargetTimeBefore, getGfsTargetTimeAfter, fetchGfsForecast } from '../helpers/gfs';

function* fetchZoneHistory(action) {
  const { zoneId, features } = action.payload;
  let endpoint = `/v4/history?countryCode=${zoneId}`;

  if (features.length > 0) {
    endpoint += `${features.map((f) => `&${f}=true`)}`;
  }

  try {
    const payload = yield call(protectedJsonRequest, endpoint);
    yield put({ type: 'ZONE_HISTORY_FETCH_SUCCEEDED', zoneId, payload });
  } catch (err) {
    yield put({ type: 'ZONE_HISTORY_FETCH_FAILED' });
    handleRequestError(err);
  }
}

function* fetchGridData(action) {
  const features = action.payload.features || [];
  let endpoint = '/v4/state';

  if (features.includes('history')) {
    endpoint = '/v5/state/hourly';
  }

  if (features.length > 0) {
    endpoint += `?featureflag=true${features.map((f) => `&${f}=true`)}`;
  }

  try {
    const payload = yield call(protectedJsonRequest, endpoint);
    yield put({ type: 'APPLICATION_STATE_UPDATE', key: 'callerLocation', value: payload.callerLocation });
    yield put({ type: 'GRID_DATA_FETCH_SUCCEEDED', payload });
  } catch (err) {
    yield put({ type: 'GRID_DATA_FETCH_FAILED' });
    handleRequestError(err);
  }
}

function* fetchSolarData(action) {
  const { datetime } = action.payload || {};
  try {
    const before = yield call(fetchGfsForecast, 'solar', getGfsTargetTimeBefore(datetime));
    const after = yield call(fetchGfsForecast, 'solar', getGfsTargetTimeAfter(datetime));
    yield put({ type: 'SOLAR_DATA_FETCH_SUCCEEDED', payload: { forecasts: [before, after] } });
  } catch (err) {
    yield put({ type: 'SOLAR_DATA_FETCH_FAILED' });
    handleRequestError(err);
  }
}

function* fetchWindData(action) {
  const { datetime } = action.payload || {};
  try {
    const before = yield call(fetchGfsForecast, 'wind', getGfsTargetTimeBefore(datetime));
    const after = yield call(fetchGfsForecast, 'wind', getGfsTargetTimeAfter(datetime));
    yield put({ type: 'WIND_DATA_FETCH_SUCCEEDED', payload: { forecasts: [before, after] } });
  } catch (err) {
    yield put({ type: 'WIND_DATA_FETCH_FAILED' });
    handleRequestError(err);
  }
}

function* trackEvent(action) {
  const { eventName, context = {} } = action.payload;

  yield call([thirdPartyServices, thirdPartyServices.trackEvent], eventName, {
    ...context,
  });
}

export default function* () {
  // Data fetching
  yield takeLatest('GRID_DATA_FETCH_REQUESTED', fetchGridData);
  yield takeLatest('WIND_DATA_FETCH_REQUESTED', fetchWindData);
  yield takeLatest('SOLAR_DATA_FETCH_REQUESTED', fetchSolarData);
  yield takeLatest('ZONE_HISTORY_FETCH_REQUESTED', fetchZoneHistory);
  // Analytics
  yield takeLatest('TRACK_EVENT', trackEvent);
}
