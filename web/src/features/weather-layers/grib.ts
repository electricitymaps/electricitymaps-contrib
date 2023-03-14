import type { ForecastEntry } from 'api/getWeatherData';
import { addHours } from 'date-fns';

export function getReferenceTime(grib: ForecastEntry) {
  return new Date(grib.header.refTime);
}

export function getTargetTime(grib: ForecastEntry) {
  return addHours(getReferenceTime(grib), grib.header.forecastTime).getTime();
}
