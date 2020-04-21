import { call, put, takeLatest } from 'redux-saga/effects';
import moment from 'moment';

import thirdPartyServices from '../services/thirdparty';
import { handleRequestError, protectedJsonRequest, textRequest } from '../helpers/api';
import {
  getGfsTargetTimeBefore,
  getGfsTargetTimeAfter,
  fetchGfsForecast,
} from '../helpers/gfs';
import { TIMESCALE } from '../helpers/constants';

function* fetchClientVersion(action) {
  try {
    const version = yield call(textRequest, '/clientVersion');
    yield put({ type: 'APPLICATION_STATE_UPDATE', key: 'version', value: version });
  } catch (err) {
    handleRequestError(err);
  }
}

function* fetchZoneHistory(action) {
  const { zoneId, timescale } = action.payload;
  try {
    let path = `/v3/history?countryCode=${zoneId}`;
    if (timescale !== TIMESCALE.LIVE) {
      path += `&timescale=${timescale}`;
    }
    const payload = yield call(protectedJsonRequest, path);
    yield put({ type: 'ZONE_HISTORY_FETCH_SUCCEEDED', zoneId, payload });
  } catch (err) {
    yield put({ type: 'ZONE_HISTORY_FETCH_FAILED' });
    handleRequestError(err);
  }
}

function* fetchGridData(action) {
  const { datetime, timescale } = action.payload;
  try {
    let path = datetime ? `/v3/state?datetime=${datetime}` : '/v3/state';
    if (timescale !== TIMESCALE.LIVE) {
      path += `?timescale=${timescale}_${moment().startOf('month').subtract(1, 'month').format('YYYYMM')}`;
    }
    const payload = yield call(protectedJsonRequest, path);
    thirdPartyServices.trackWithCurrentApplicationState('pageview');
    yield put({ type: 'APPLICATION_STATE_UPDATE', key: 'callerLocation', value: payload.callerLocation });
    yield put({ type: 'APPLICATION_STATE_UPDATE', key: 'callerZone', value: payload.callerZone });
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

export default function* () {
  yield takeLatest('GRID_DATA_FETCH_REQUESTED', fetchGridData);
  yield takeLatest('WIND_DATA_FETCH_REQUESTED', fetchWindData);
  yield takeLatest('SOLAR_DATA_FETCH_REQUESTED', fetchSolarData);
  yield takeLatest('ZONE_HISTORY_FETCH_REQUESTED', fetchZoneHistory);
  yield takeLatest('CLIENT_VERSION_FETCH_REQUESTED', fetchClientVersion);
}
