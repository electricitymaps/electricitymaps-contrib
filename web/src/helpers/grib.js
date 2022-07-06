import { addHours } from 'date-fns';

export function getRefTime(grib) {
  return new Date(grib.header.refTime);
}

export function getTargetTime(grib) {
  return addHours(getRefTime(grib), grib.header.forecastTime);
}

export function getValueAtPosition(longitude, latitude, grib) {
  if (!grib) {
    return null;
  }
  const i = Math.floor(longitude - grib.header.lo1) / grib.header.dx;
  const j = Math.floor(grib.header.la1 - latitude) / grib.header.dy;
  const n = j * grib.header.nx + i;
  return grib.data[n];
}
