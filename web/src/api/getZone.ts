import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import invariant from 'tiny-invariant';
import type { ZoneDetails } from 'types';
import { RouteParameters } from 'types';
import { TimeRange } from 'utils/constants';
import { memoizedIsValidHistoricalTimeRange } from 'utils/helpers';
import { getStaleTime } from 'utils/refetching';

import {
  cacheBuster,
  getBasePath,
  getHeaders,
  isValidDate,
  QUERY_KEYS,
  TIME_RANGE_TO_TIME_AVERAGE,
} from './helpers';

const getZone = async (
  timeRange: TimeRange,
  zoneId: string,
  targetDatetime?: string
): Promise<ZoneDetails> => {
  invariant(zoneId, 'Zone ID is required');

  const shouldQueryHistorical =
    targetDatetime &&
    isValidDate(targetDatetime) &&
    memoizedIsValidHistoricalTimeRange(timeRange);

  const path: URL = new URL(
    `v9/details/${TIME_RANGE_TO_TIME_AVERAGE[timeRange]}/${zoneId}${
      shouldQueryHistorical ? `?targetDate=${targetDatetime}` : ''
    }`,
    getBasePath()
  );
  if (!targetDatetime) {
    path.searchParams.append('cacheKey', cacheBuster());
  }
  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  const response = await fetch(path, requestOptions);

  if (response.ok) {
    const { data } = (await response.json()) as { data: ZoneDetails };
    if (!data.zoneStates) {
      throw new Error('No data returned from API');
    }
    return data;
  }

  throw new Error(await response.text());
};

const useGetZone = (): UseQueryResult<ZoneDetails> => {
  const { zoneId, urlTimeRange, urlDatetime } = useParams<RouteParameters>();

  const timeRange = urlTimeRange || TimeRange.H72;
  return useQuery<ZoneDetails>({
    queryKey: [
      QUERY_KEYS.ZONE,
      {
        zone: zoneId,
        aggregate: timeRange,
        targetDatetime: urlDatetime,
      },
    ],
    queryFn: async () => {
      if (!zoneId) {
        throw new Error('Zone ID is required');
      }
      return getZone(timeRange, zoneId, urlDatetime);
    },
    staleTime: getStaleTime(timeRange, urlDatetime),
    refetchOnWindowFocus: true,
  });
};

export default useGetZone;
