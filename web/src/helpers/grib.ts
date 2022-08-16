import { addHours } from 'date-fns';

export function getRefTime(grib: any) {
  return new Date(grib.header.refTime);
}

export function getTargetTime(grib: any) {
  return addHours(getRefTime(grib), grib.header.forecastTime);
}

export function getValueAtPosition(longitude: any, latitude: any, grib: any) {
  if (!grib) {
    return null;
  }
  const i = Math.floor(longitude - grib.header.lo1) / grib.header.dx;
  const j = Math.floor(grib.header.la1 - latitude) / grib.header.dy;
  const n = j * grib.header.nx + i;
  return grib.data[n];
}
