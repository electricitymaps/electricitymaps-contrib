import { call, put, takeLatest } from 'redux-saga/effects';

import thirdPartyServices from '../services/thirdparty';
import { handleRequestError, protectedJsonRequest } from '../helpers/api';
import { getGfsTargetTimeBefore, getGfsTargetTimeAfter, fetchGfsForecast } from '../helpers/gfs';
import {
  GRID_DATA_FETCH_FAILED,
  GRID_DATA_FETCH_REQUESTED,
  GRID_DATA_FETCH_SUCCEEDED,
  SOLAR_DATA_FETCH_FAILED,
  SOLAR_DATA_FETCH_REQUESTED,
  SOLAR_DATA_FETCH_SUCCEDED,
  WIND_DATA_FETCH_FAILED,
  WIND_DATA_FETCH_REQUESTED,
  WIND_DATA_FETCH_SUCCEDED,
  ZONE_HISTORY_FETCH_FAILED,
  ZONE_HISTORY_FETCH_REQUESTED,
  ZONE_HISTORY_FETCH_SUCCEEDED,
} from '../helpers/redux';

function* fetchZoneHistory(action: any) {
  const { zoneId, features, selectedTimeAggregate } = action.payload;
  let endpoint = `/v5/history/${selectedTimeAggregate}?countryCode=${zoneId}`;

  if (features.length > 0) {
    endpoint += `${features.map((f: any) => `&${f}=true`)}`;
  }

  try {
    // @ts-expect-error TS(7057): 'yield' expression implicitly results in an 'any' ... Remove this comment to see the full error message
    const payload = yield call(protectedJsonRequest, endpoint);
    // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
    yield put(ZONE_HISTORY_FETCH_SUCCEEDED({ ...payload, zoneId }));
  } catch (err) {
    yield put(ZONE_HISTORY_FETCH_FAILED());
    handleRequestError(err);
  }
}

function* fetchGridData(action: any) {
  const { features, selectedTimeAggregate } = action.payload;
  let endpoint = `/v5/state/${selectedTimeAggregate}`;

  if (features.length > 0) {
    endpoint += `?featureflag=true${features.map((f: any) => `&${f}=true`)}`;
  }

  try {
    // @ts-expect-error TS(7057): 'yield' expression implicitly results in an 'any' ... Remove this comment to see the full error message
    const payload = yield call(protectedJsonRequest, endpoint);
    yield put({ type: 'APPLICATION_STATE_UPDATE', key: 'callerLocation', value: payload.callerLocation });
    // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
    yield put(GRID_DATA_FETCH_SUCCEEDED(payload));
    yield put({ type: 'APPLICATION_STATE_UPDATE', key: 'selectedZoneTimeIndex', value: payload.datetimes.length - 1 });
  } catch (err) {
    yield put(GRID_DATA_FETCH_FAILED());
    handleRequestError(err);
  }
}

function* fetchSolarData(action: any) {
  const { datetime } = action.payload || {};
  try {
    // @ts-expect-error TS(7057): 'yield' expression implicitly results in an 'any' ... Remove this comment to see the full error message
    const before = yield call(fetchGfsForecast, 'solar', getGfsTargetTimeBefore(datetime));
    // @ts-expect-error TS(7057): 'yield' expression implicitly results in an 'any' ... Remove this comment to see the full error message
    const after = yield call(fetchGfsForecast, 'solar', getGfsTargetTimeAfter(datetime));
    // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
    yield put(SOLAR_DATA_FETCH_SUCCEDED({ forecasts: [before, after] }));
  } catch (err) {
    yield put(SOLAR_DATA_FETCH_FAILED());
    handleRequestError(err);
  }
}

function* fetchWindData(action: any) {
  const { datetime } = action.payload || {};
  try {
    // @ts-expect-error TS(7057): 'yield' expression implicitly results in an 'any' ... Remove this comment to see the full error message
    const before = yield call(fetchGfsForecast, 'wind', getGfsTargetTimeBefore(datetime));
    // @ts-expect-error TS(7057): 'yield' expression implicitly results in an 'any' ... Remove this comment to see the full error message
    const after = yield call(fetchGfsForecast, 'wind', getGfsTargetTimeAfter(datetime));
    // @ts-expect-error TS(2554): Expected 0 arguments, but got 1.
    yield put(WIND_DATA_FETCH_SUCCEDED({ forecasts: [before, after] }));
  } catch (err) {
    yield put(WIND_DATA_FETCH_FAILED());
    handleRequestError(err);
  }
}

function* trackEvent(action: any) {
  const { eventName, context = {} } = action.payload;

  yield call([thirdPartyServices, thirdPartyServices.trackEvent], eventName, {
    ...context,
  });
}

export default function* () {
  // Data fetching
  yield takeLatest(GRID_DATA_FETCH_REQUESTED, fetchGridData);
  yield takeLatest(WIND_DATA_FETCH_REQUESTED, fetchWindData);
  yield takeLatest(SOLAR_DATA_FETCH_REQUESTED, fetchSolarData);
  yield takeLatest(ZONE_HISTORY_FETCH_REQUESTED, fetchZoneHistory);
  // Analytics
  yield takeLatest('TRACK_EVENT', trackEvent);
}
