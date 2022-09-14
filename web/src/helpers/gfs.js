import { addHours, formatISO, getHours, startOfHour, subHours } from 'date-fns';

import { protectedJsonRequest } from './api';

const GFS_STEP_ORIGIN = 6; // hours
const GFS_STEP_HORIZON = 1; // hours

export function getGfsTargetTimeBefore(datetime) {
  let horizon = startOfHour(datetime ?? new Date());
  while (getHours(horizon) % GFS_STEP_HORIZON !== 0) {
    horizon = subHours(horizon, 1);
  }
  return horizon;
}

export function getGfsTargetTimeAfter(datetime) {
  return addHours(getGfsTargetTimeBefore(datetime), GFS_STEP_HORIZON);
}

function getGfsRefTimeForTarget(datetime) {
  // Warning: solar will not be available at horizon 0 so always do at least horizon 1
  let origin = subHours(datetime, 1);
  while (getHours(origin) % GFS_STEP_ORIGIN !== 0) {
    origin = subHours(origin, 1);
  }
  return origin;
}

export function fetchGfsForecast(resource, targetTime) {
  const requestForecastAtRef = (refTime) =>
    protectedJsonRequest(`/v3/gfs/${resource}?refTime=${formatISO(refTime)}&targetTime=${formatISO(targetTime)}`);
  // Try fetching the forecast at the given timestamp and if it fails, try one more time.
  return new Promise((resolve, reject) => {
    requestForecastAtRef(getGfsRefTimeForTarget(targetTime))
      .then(resolve)
      .catch(() => {
        requestForecastAtRef(subHours(getGfsRefTimeForTarget(targetTime), GFS_STEP_ORIGIN))
          .then(resolve)
          .catch(reject);
      });
  });
}
