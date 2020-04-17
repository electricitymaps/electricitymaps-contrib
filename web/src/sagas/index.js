import { call, put, takeLatest } from 'redux-saga/effects';

import * as LoadingService from '../services/loadingservice';
import { protectedJsonRequest } from '../helpers/api';

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

export default function* () {
  yield takeLatest('ZONE_HISTORY_FETCH_REQUESTED', fetchZoneHistory);
}
