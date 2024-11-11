import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import type { GridState } from 'types';
import { TimeAverages, UrlTimeAverages } from 'utils/constants';
import { URL_TO_TIME_AVERAGE } from 'utils/state/atoms';

import { cacheBuster, getBasePath, isValidDate, QUERY_KEYS } from './helpers';

const getState = async (
  timeAverage: TimeAverages | 'last_hour',
  targetDatetime?: string
): Promise<GridState> => {
  const shouldQueryHistorical =
    targetDatetime && isValidDate(targetDatetime) && timeAverage === TimeAverages.HOURLY;
  const path: URL = new URL(
    `v8/state/${timeAverage}${
      shouldQueryHistorical ? `?targetDate=${targetDatetime}` : ''
    }`,
    getBasePath()
  );

  !targetDatetime && path.searchParams.append('cacheKey', cacheBuster());
  const response = await fetch(path);
  if (response.ok) {
    const result = (await response.json()) as GridState;
    return result;
  }

  throw new Error(await response.text());
};

const useGetState = (): UseQueryResult<GridState> => {
  const queryClient = useQueryClient();
  const { urlTimeAverage, urlDatetime } = useParams<{
    urlTimeAverage: UrlTimeAverages;
    urlDatetime?: string;
  }>();
  console.log('urlDatetime', urlDatetime);
  const isHourly = urlTimeAverage === UrlTimeAverages['24h'];
  const shouldUseLastHour = isHourly && !urlDatetime;
  const timeAverage = urlTimeAverage
    ? URL_TO_TIME_AVERAGE[urlTimeAverage]
    : TimeAverages.HOURLY;
  const lastHourQuery = useQuery<GridState>({
    queryKey: [QUERY_KEYS.STATE, { aggregate: 'last_hour' }],
    queryFn: () => getState('last_hour'),
    enabled: shouldUseLastHour,
  });

  const fullDataQuery = useQuery<GridState>({
    queryKey: [
      QUERY_KEYS.STATE,
      {
        aggregate: timeAverage,
        targetDatetime: urlDatetime,
      },
    ],
    queryFn: () => getState(timeAverage, urlDatetime),
    enabled: !shouldUseLastHour || (shouldUseLastHour && lastHourQuery.isSuccess),
  });

  useEffect(() => {
    if (shouldUseLastHour && fullDataQuery.data) {
      queryClient.setQueryData(
        [QUERY_KEYS.STATE, { aggregate: 'last_hour' }],
        fullDataQuery.data
      );
    }
  }, [shouldUseLastHour, fullDataQuery.data, queryClient]);

  if (shouldUseLastHour) {
    if (!fullDataQuery.data && lastHourQuery.data) {
      return lastHourQuery;
    }
    return fullDataQuery;
  }

  return fullDataQuery;
};

export default useGetState;
