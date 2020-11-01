import moment from 'moment';

export function getRefTime(grib) {
  return moment(grib.header.refTime);
}

export function getTargetTime(grib) {
  return moment(getRefTime(grib)).add(grib.header.forecastTime, 'hour');
}

export function getValueAtPosition(longitude, latitude, grib) {
  if (!grib) return null;
  const i = Math.floor(longitude - grib.header.lo1) / grib.header.dx;
  const j = Math.floor(grib.header.la1 - latitude) / grib.header.dy;
  const n = j * grib.header.nx + i;
  return grib.data[n];
}
