import moment from 'moment';

const GFS_STEP_ORIGIN = 6; // hours
const GFS_STEP_HORIZON = 1; // hours

export function getGfsTargetTimeBefore(datetime) {
  let horizon = moment(datetime).utc().startOf('hour');
  while ((horizon.hour() % GFS_STEP_HORIZON) !== 0) {
    horizon = horizon.subtract(1, 'hour');
  }
  return horizon;
}

export function getGfsTargetTimeAfter(datetime) {
  return moment(getGfsTargetTimeBefore(datetime)).add(GFS_STEP_HORIZON, 'hour');
}

export function getGfsRefTimeForTarget(datetime) {
  // Warning: solar will not be available at horizon 0 so always do at least horizon 1
  let origin = moment(datetime).subtract(1, 'hour');
  while ((origin.hour() % GFS_STEP_ORIGIN) !== 0) {
    origin = origin.subtract(1, 'hour');
  }
  return origin;
}
