import moment from 'moment';

import { protectedJsonRequest } from './api';

const GFS_STEP_ORIGIN = 6; // hours
const GFS_STEP_HORIZON = 1; // hours

export function getGfsTargetTimeBefore(datetime, modulo=GFS_STEP_HORIZON) {
  let horizon = moment(datetime).utc().startOf('hour');
  while ((horizon.hour() % modulo) !== 0) {
    horizon = horizon.subtract(1, 'hour');
  }
  return horizon;
}

export function getGfsTargetTimeAfter(datetime, modulo=GFS_STEP_HORIZON) {
  let horizon = moment(datetime).utc().add(1, 'hour').startOf('hour');
  while ((horizon.hour() % modulo) !== 0) {
    horizon = horizon.add(1, 'hour');
  }
  return horizon;
}

function getGfsRefTimeForTarget(datetime) {
  // Warning: solar will not be available at horizon 0 so always do at least horizon 1
  let origin = moment(datetime).subtract(1, 'hour');
  while ((origin.hour() % GFS_STEP_ORIGIN) !== 0) {
    origin = origin.subtract(1, 'hour');
  }
  return origin;
}

export function fetchGfsForecast(resource, targetTime) {
  const requestForecastAtRef = refTime => (
    protectedJsonRequest(`/v3/gfs/${resource}?refTime=${refTime.toISOString()}&targetTime=${targetTime.toISOString()}`)
  );
  // Try fetching the forecast at the given timestamp and if it fails, try one more time.
  return new Promise((resolve, reject) => {
    requestForecastAtRef(getGfsRefTimeForTarget(targetTime))
      .then(resolve)
      .catch(() => {
        requestForecastAtRef(getGfsRefTimeForTarget(targetTime).subtract(GFS_STEP_ORIGIN, 'hour'))
          .then(resolve)
          .catch(reject);
      });
  });
}
