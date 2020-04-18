import {
  call,
  put,
  select,
  takeLatest,
} from 'redux-saga/effects';

import thirdPartyServices from '../services/thirdparty';
import * as LoadingService from '../services/loadingservice';
import { handleConnectionReturnCode, protectedJsonRequest } from '../helpers/api';

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

export default function* () {
  yield takeLatest('GRID_DATA_FETCH_REQUESTED', fetchGridData);
  yield takeLatest('ZONE_HISTORY_FETCH_REQUESTED', fetchZoneHistory);
}
