import { interpolate } from 'd3-interpolate';
import { formatDistance } from 'date-fns';

import { GfsForecastResponse } from 'api/getWeatherData';
import { Maybe } from 'types';
import { getRefTime as getReferenceTime, getTargetTime } from './grib';

export function useInterpolatedWindData(
  windData: GfsForecastResponse[]
): Maybe<GfsForecastResponse> {
  if (!windData) {
    return null;
  }

  const gribs1 = windData[0];
  const gribs2 = windData[1];
  const tBefore = getTargetTime(gribs1[0]);
  const tAfter = getTargetTime(gribs2[0]);
  const datetime = new Date();
  const k = (datetime - tBefore) / (tAfter - tBefore);
  if (datetime > tAfter) {
    console.error('Error while interpolating wind because current time is out of bounds');
    return null;
  }
  console.info(
    `#1 wind forecast target ${formatDistance(tBefore, new Date(), {
      addSuffix: true,
    })} made ${formatDistance(getReferenceTime(gribs1[0]), new Date(), {
      addSuffix: true,
    })}`
  );

  console.info(
    `#2 wind forecast target ${formatDistance(tAfter, new Date(), {
      addSuffix: true,
    })} made ${formatDistance(getReferenceTime(gribs2[0]), new Date(), {
      addSuffix: true,
    })}`
  );

  return [
    {
      ...gribs1[0],
      data: gribs1[0].data.map((d, index) => interpolate(d, gribs2[0].data[index])(k)),
    },
    {
      ...gribs1[1],
      data: gribs1[1].data.map((d, index) => interpolate(d, gribs2[1].data[index])(k)),
    },
  ];
}

export function useInterpolatedSolarData() {
  const solarData = {}; //get solar data

  // TODO: Recalculate every 5 minutes if custom datetime is not set.

  if (!solarData || !solarData.forecasts) {
    return null;
  }

  const grib1 = solarData.forecasts[0];
  const grib2 = solarData.forecasts[1];
  const tBefore = getTargetTime(grib1);
  const tAfter = getTargetTime(grib2);
  const datetime = new Date();
  const k = (datetime - tBefore) / (tAfter - tBefore);

  if (datetime > tAfter) {
    console.error(
      'Error while interpolating solar because current time is out of bounds'
    );
    return null;
  }

  console.info(
    `#1 solar forecast target ${formatDistance(tBefore, new Date(), {
      addSuffix: true,
    })} made ${formatDistance(getReferenceTime(grib1), new Date(), {
      addSuffix: true,
    })}`
  );

  console.info(
    `#2 solar forecast target ${formatDistance(tAfter, new Date(), {
      addSuffix: true,
    })} made ${formatDistance(getReferenceTime(grib2), new Date(), {
      addSuffix: true,
    })}`
  );

  return {
    ...grib1,
    data: grib1.data.map((d, index) => interpolate(d, grib2.data[index])(k)),
  };
}
