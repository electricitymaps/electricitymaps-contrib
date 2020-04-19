import {
  call,
  put,
  select,
  takeLatest,
} from 'redux-saga/effects';

import thirdPartyServices from '../services/thirdparty';
import * as LoadingService from '../services/loadingservice';
import { handleConnectionReturnCode, protectedJsonRequest, textRequest } from '../helpers/api';
import {
  getGfsTargetTimeBefore,
  getGfsTargetTimeAfter,
  fetchGfsForecast,
} from '../helpers/gfs';

function* fetchZoneHistory(action) {
  const { zoneId } = action.payload;
  LoadingService.startLoading('.country-history .loading');
  try {
    const payload = yield call(protectedJsonRequest, `/v3/history?countryCode=${zoneId}`);
    yield put({ type: 'ZONE_HISTORY_FETCH_SUCCEEDED', zoneId, payload });
  } catch (error) {
    yield put({ type: 'ZONE_HISTORY_FETCH_FAILED', error });
  }
  LoadingService.stopLoading('.country-history .loading');
}

function* fetchGridData(action) {
  const { datetime, showLoading } = action.payload;
  if (showLoading) LoadingService.startLoading('#loading');
  LoadingService.startLoading('#small-loading');
  try {
    const payload = yield call(protectedJsonRequest, datetime ? `/v3/state?datetime=${datetime}` : '/v3/state');
    thirdPartyServices.trackWithCurrentApplicationState('pageview');
    yield put({ type: 'APPLICATION_STATE_UPDATE', key: 'callerLocation', value: payload.callerLocation });
    yield put({ type: 'APPLICATION_STATE_UPDATE', key: 'callerZone', value: payload.callerZone });
    yield put({ type: 'APPLICATION_STATE_UPDATE', key: 'showConnectionWarning', value: false });
    yield put({ type: 'GRID_DATA_FETCH_SUCCEEDED', payload });
  } catch (error) {
    const appState = yield select(state => state.application);
    handleConnectionReturnCode(error, appState);
    yield put({ type: 'APPLICATION_STATE_UPDATE', key: 'showConnectionWarning', value: true });
    yield put({ type: 'GRID_DATA_FETCH_FAILED', error });
  }
  if (showLoading) LoadingService.stopLoading('#loading');
  LoadingService.stopLoading('#small-loading');
}

function* fetchClientVersion(action) {
  try {
    const version = yield call(textRequest, '/clientVersion');
    yield put({ type: 'APPLICATION_STATE_UPDATE', key: 'version', value: version });
  } catch (error) {
    const appState = yield select(state => state.application);
    handleConnectionReturnCode(error, appState);
  }
}

// TODO: Try datetime.subtract(GFS_STEP_ORIGIN, 'hour') once if the first attempt doesn't work.
function* fetchSolarData(action) {
  const { datetime, showLoading } = action.payload;
  if (showLoading) LoadingService.startLoading('#loading');
  LoadingService.startLoading('#small-loading');
  try {
    const before = yield call(fetchGfsForecast, 'solar', getGfsTargetTimeBefore(datetime));
    const after = yield call(fetchGfsForecast, 'solar', getGfsTargetTimeAfter(datetime));
    yield put({ type: 'SOLAR_DATA_FETCH_SUCCEEDED', payload: { forecasts: [before, after] } });
  } catch (error) {
    const appState = yield select(state => state.application);
    handleConnectionReturnCode(error, appState);
  }
  if (showLoading) LoadingService.stopLoading('#loading');
  LoadingService.stopLoading('#small-loading');
}

// TODO: Try datetime.subtract(GFS_STEP_ORIGIN, 'hour') once if the first attempt doesn't work.
function* fetchWindData(action) {
  const { datetime, showLoading } = action.payload;
  if (showLoading) LoadingService.startLoading('#loading');
  LoadingService.startLoading('#small-loading');
  try {
    const before = yield call(fetchGfsForecast, 'wind', getGfsTargetTimeBefore(datetime));
    const after = yield call(fetchGfsForecast, 'wind', getGfsTargetTimeAfter(datetime));
    yield put({ type: 'WIND_DATA_FETCH_SUCCEEDED', payload: { forecasts: [before, after] } });
  } catch (error) {
    const appState = yield select(state => state.application);
    handleConnectionReturnCode(error, appState);
  }
  if (showLoading) LoadingService.stopLoading('#loading');
  LoadingService.stopLoading('#small-loading');
}

export default function* () {
  yield takeLatest('GRID_DATA_FETCH_REQUESTED', fetchGridData);
  yield takeLatest('WIND_DATA_FETCH_REQUESTED', fetchWindData);
  yield takeLatest('SOLAR_DATA_FETCH_REQUESTED', fetchSolarData);
  yield takeLatest('ZONE_HISTORY_FETCH_REQUESTED', fetchZoneHistory);
  yield takeLatest('CLIENT_VERSION_FETCH_REQUESTED', fetchClientVersion);
}
