import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useAtomValue } from 'jotai';
import { useParams } from 'react-router-dom';
import invariant from 'tiny-invariant';
import type { ZoneDetails } from 'types';
import { RouteParameters } from 'types';
import { TimeRange } from 'utils/constants';
import { isValidHistoricalTimeRange } from 'utils/helpers';
import { getStaleTime } from 'utils/refetching';
import { timeRangeAtom } from 'utils/state/atoms';

import {
  cacheBuster,
  getBasePath,
  getHeaders,
  getParameters,
  isValidDate,
  QUERY_KEYS,
  TIME_RANGE_TO_BACKEND_PATH,
} from './helpers';

const getAggregatedFranceData = async (): Promise<any> => {
  const response = await fetch('/api/aggregate-france', {
    method: 'GET',
  });

  if (response.ok) {
    return response.json();
  }

  throw new Error('Failed to fetch aggregated France data');
};

const getZone = async (
  timeRange: TimeRange,
  zoneId: string,
  is1HourAppDelay: boolean,
  targetDatetime?: string
): Promise<ZoneDetails> => {
  invariant(zoneId, 'Zone ID is required');

  if (zoneId === 'FR') {
    // Fetch aggregated France data if the zone is France
    return getAggregatedFranceData();
  }

  const shouldQueryHistorical =
    targetDatetime &&
    isValidDate(targetDatetime) &&
    isValidHistoricalTimeRange(timeRange);

  const path: URL = new URL(
    `v10/details/${TIME_RANGE_TO_BACKEND_PATH[timeRange]}/${zoneId}${getParameters(
      shouldQueryHistorical,
      is1HourAppDelay,
      targetDatetime
    )}`,
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
    const data = (await response.json()) as ZoneDetails;
    if (!data.zoneStates) {
      throw new Error('No data returned from API');
    }
    return data;
  }

  throw new Error(await response.text());
};

const useGetZone = (): UseQueryResult<ZoneDetails> => {
  const { zoneId, urlDatetime } = useParams<RouteParameters>();
  const timeRange = useAtomValue(timeRangeAtom);

  const is1HourAppDelay = useFeatureFlag('1-hour-app-delay');

  return useQuery<ZoneDetails>({
    queryKey: [
      QUERY_KEYS.ZONE,
      {
        zone: zoneId,
        aggregate: timeRange,
        targetDatetime: urlDatetime,
        is1HourAppDelay,
      },
    ],
    queryFn: async () => {
      if (!zoneId) {
        throw new Error('Zone ID is required');
      }
      return getZone(timeRange, zoneId, is1HourAppDelay, urlDatetime);
    },
    staleTime: getStaleTime(timeRange, urlDatetime),
    refetchOnWindowFocus: true,
  });
};

export default useGetZone;
