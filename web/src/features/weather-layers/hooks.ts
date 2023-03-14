import { interpolate } from 'd3-interpolate';
import { formatDistance } from 'date-fns';

import { GfsForecastResponse, WeatherType } from 'api/getWeatherData';
import { Maybe } from 'types';
import { getReferenceTime, getTargetTime } from './grib';

export function useInterpolatedData(
  type: WeatherType,
  rawData: GfsForecastResponse[]
): Maybe<GfsForecastResponse> {
  // TODO: Recalculate every 5 minutes if custom datetime is not set.
  // TODO: Consider using this as a hook so we can memo it

  if (!rawData) {
    return null;
  }

  const gribs1 = rawData[0];
  const gribs2 = rawData[1];
  const tBefore = getTargetTime(gribs1[0]);
  const tAfter = getTargetTime(gribs2[0]);
  const datetime = Date.now();
  const k = (datetime - tBefore) / (tAfter - tBefore);
  if (datetime > tAfter) {
    console.error(
      `Error while interpolating ${type} because current time is out of bounds`
    );
    return null;
  }
  console.info(
    `#1 ${type} forecast target ${formatDistance(tBefore, new Date(), {
      addSuffix: true,
    })} made ${formatDistance(getReferenceTime(gribs1[0]), new Date(), {
      addSuffix: true,
    })}`
  );

  console.info(
    `#2 ${type} forecast target ${formatDistance(tAfter, new Date(), {
      addSuffix: true,
    })} made ${formatDistance(getReferenceTime(gribs2[0]), new Date(), {
      addSuffix: true,
    })}`
  );

  return gribs1.map((grib, outerIndex) => ({
    ...grib,
    data: grib.data.map((d, index) => interpolate(d, gribs2[outerIndex].data[index])(k)),
  }));
}
