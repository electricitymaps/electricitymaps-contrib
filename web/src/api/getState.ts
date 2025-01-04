import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import type { GridState, RouteParameters } from 'types';
import { TimeRange } from 'utils/constants';
import { isValidHistoricalTimeRange } from 'utils/helpers';
import { getStaleTime } from 'utils/refetching';

import {
  cacheBuster,
  getBasePath,
  getHeaders,
  isValidDate,
  QUERY_KEYS,
  TIME_RANGE_TO_TIME_AVERAGE,
} from './helpers';

const getState = async (
  timeRange: TimeRange,
  targetDatetime?: string
): Promise<GridState> => {
  const shouldQueryHistorical =
    targetDatetime &&
    isValidDate(targetDatetime) &&
    isValidHistoricalTimeRange(timeRange);

  const path: URL = new URL(
    `v9/state/${TIME_RANGE_TO_TIME_AVERAGE[timeRange]}${
      shouldQueryHistorical ? `?targetDate=${targetDatetime}` : ''
    }`,
    getBasePath()
  );

  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  if (!targetDatetime) {
    path.searchParams.append('cacheKey', cacheBuster());
  }
  const response = await fetch(path, requestOptions);
  if (response.ok) {
    const result = (await response.json()) as GridState;
    return result;
  }

  throw new Error(await response.text());
};

const useGetState = (): UseQueryResult<GridState> => {
  const { urlTimeRange, urlDatetime } = useParams<RouteParameters>();
  const timeRange = urlTimeRange || TimeRange.H72;
  return useQuery<GridState>({
    queryKey: [
      QUERY_KEYS.STATE,
      {
        aggregate: timeRange,
        targetDatetime: urlDatetime,
      },
    ],
    queryFn: () => getState(timeRange, urlDatetime),
    staleTime: getStaleTime(timeRange, urlDatetime),
    refetchOnWindowFocus: true,
  });
};

export default useGetState;
