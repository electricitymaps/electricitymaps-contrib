import moment from 'moment';

import { protectedJsonRequest } from './api';

const GFS_STEP_ORIGIN = 6; // hours
const GFS_STEP_HORIZON = 1; // hours

export function getGfsTargetTimeBefore(datetime: any) {
  let horizon = moment(datetime).utc().startOf('hour');
  while (horizon.hour() % GFS_STEP_HORIZON !== 0) {
    horizon = horizon.subtract(1, 'hour');
  }
  return horizon;
}

export function getGfsTargetTimeAfter(datetime: any) {
  return moment(getGfsTargetTimeBefore(datetime)).add(GFS_STEP_HORIZON, 'hour');
}

function getGfsRefTimeForTarget(datetime: any) {
  // Warning: solar will not be available at horizon 0 so always do at least horizon 1
  let origin = moment(datetime).subtract(1, 'hour');
  while (origin.hour() % GFS_STEP_ORIGIN !== 0) {
    origin = origin.subtract(1, 'hour');
  }
  return origin;
}

export function fetchGfsForecast(resource: any, targetTime: any) {
  const requestForecastAtRef = (refTime: any) =>
    protectedJsonRequest(`/v3/gfs/${resource}?refTime=${refTime.toISOString()}&targetTime=${targetTime.toISOString()}`);
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
