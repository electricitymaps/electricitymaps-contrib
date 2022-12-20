import { addHours } from 'date-fns';

export function getReferenceTime(grib) {
  return new Date(grib.header.refTime);
}

export function getTargetTime(grib) {
  return addHours(getReferenceTime(grib), grib.header.forecastTime);
}

export function getValueAtPosition(longitude, latitude, grib) {
  if (!grib) {
    return null;
  }
  const index = Math.floor(longitude - grib.header.lo1) / grib.header.dx;
  const index_ = Math.floor(grib.header.la1 - latitude) / grib.header.dy;
  const n = index_ * grib.header.nx + index;
  return grib.data[n];
}
