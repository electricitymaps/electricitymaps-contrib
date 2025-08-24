import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
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

const getZone = async (
  timeRange: TimeRange,
  zoneId: string,
  targetDatetime?: string
): Promise<ZoneDetails> => {
  invariant(zoneId, 'Zone ID is required');

  const shouldQueryHistorical =
    targetDatetime &&
    isValidDate(targetDatetime) &&
    isValidHistoricalTimeRange(timeRange);

  const path: URL = new URL(
    `v10/details/${TIME_RANGE_TO_BACKEND_PATH[timeRange]}/${zoneId}${getParameters(
      shouldQueryHistorical,
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
