import { UseQueryOptions, useQuery } from '@tanstack/react-query';
import { add, startOfHour, sub } from 'date-fns';
import { useInterpolatedWindData } from 'features/weather-layers/hooks';
import type { Maybe } from 'types';

import { REFETCH_INTERVAL_FIVE_MINUTES, getBasePath, getHeaders } from './helpers';

interface ForecastEntry {
  data: number[];
  header: {
    dx: number;
    dy: number;
    forecastTime: number;
    la1: number;
    lo1: number;
    nx: number;
    ny: number;
    parameterCategory: number;
    parameterNumber: number;
    refTime: string;
  };
}
export type GfsForecastResponse = [ForecastEntry, ForecastEntry];

const GFS_STEP_ORIGIN = 6; // hours
const GFS_STEP_HORIZON = 1; // hours

// Data is bucketed into groups for every six hours, so we need to find the closest step in the past
function getForecastStartTime(now: Date) {
  // Warning: solar will not be available at horizon 0 so always do at least horizon 1
  let origin = sub(startOfHour(now), { hours: GFS_STEP_HORIZON });
  if (origin.getUTCHours() % GFS_STEP_ORIGIN !== 0) {
    origin = getForecastStartTime(origin);
  }
  return origin;
}

function getBeforeForcastEndTime(now: Date) {
  return add(startOfHour(now), { hours: 0 }).toISOString();
}

function getAfterForecastEndTime(now: Date) {
  return add(startOfHour(now), { hours: GFS_STEP_HORIZON }).toISOString();
}

const targetTimeFunction = {
  before: getBeforeForcastEndTime,
  after: getAfterForecastEndTime,
};

export async function fetchGfsForecast(
  resource: string,
  startTime: Date,
  endTime: Date,
  type: 'before' | 'after',
  retries = 0
): Promise<GfsForecastResponse> {
  const targetTime = targetTimeFunction[type](endTime);
  const path = `/v3/gfs/${resource}?refTime=${startTime.toISOString()}&targetTime=${targetTime}`;
  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };
  const response = await fetch(`${getBasePath()}${path}`, requestOptions);
  if (response.ok) {
    const { data } = await response.json();
    return data;
  }

  if (retries >= 3 || response.status !== 404) {
    // TODO: Handle this error gracefully and show message to users that wind layer is not available
    // TODO: Log to Sentry if status is not 404
    throw new Error(
      `Failed to fetch GFS forecast after ${retries} retries (status: ${response.status})`
    );
  }

  // Retry again with a previous step date if request failed with 404
  return fetchGfsForecast(
    resource,
    sub(startTime, { hours: GFS_STEP_ORIGIN }),
    endTime,
    type,
    retries + 1
  );
}

async function getWeatherData() {
  const now = new Date();

  const startTime = getForecastStartTime(now);
  const before = fetchGfsForecast('wind', startTime, now, 'before');
  const after = fetchGfsForecast('wind', startTime, now, 'after');

  const forecasts = await Promise.all([before, after]).then((values) => {
    return values;
  });
  const interdata = useInterpolatedWindData(forecasts);

  return interdata;
}

export const useGetWind = (options?: UseQueryOptions<Maybe<GfsForecastResponse>>) => {
  return useQuery<Maybe<GfsForecastResponse>>(
    ['wind'],
    async () => await getWeatherData(),
    {
      staleTime: REFETCH_INTERVAL_FIVE_MINUTES,
      refetchOnWindowFocus: false,
      retry: false, // Disables retrying as getWeatherData handles retrying with new timestamps
      ...options,
    }
  );
};
