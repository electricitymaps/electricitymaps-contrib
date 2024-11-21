import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import type { GridState, RouteParameters } from 'types';
import { TimeAverages } from 'utils/constants';
import { isValidHistoricalTime } from 'utils/helpers';
import { URL_TO_TIME_AVERAGE } from 'utils/state/atoms';

import { cacheBuster, getBasePath, isValidDate, QUERY_KEYS } from './helpers';

const getState = async (
  timeAverage: TimeAverages,
  targetDatetime?: string
): Promise<GridState> => {
  const shouldQueryHistorical =
    targetDatetime && isValidDate(targetDatetime) && isValidHistoricalTime(timeAverage);

  const path: URL = new URL(
    `v8/state/${timeAverage}${
      shouldQueryHistorical ? `?targetDate=${targetDatetime}` : ''
    }`,
    getBasePath()
  );

  if (!targetDatetime) {
    path.searchParams.append('cacheKey', cacheBuster());
  }
  const response = await fetch(path);
  if (response.ok) {
    const result = (await response.json()) as GridState;
    return result;
  }

  throw new Error(await response.text());
};

const useGetState = (): UseQueryResult<GridState> => {
  const { urlTimeAverage, urlDatetime } = useParams<RouteParameters>();
  const timeAverage = urlTimeAverage
    ? URL_TO_TIME_AVERAGE[urlTimeAverage]
    : TimeAverages.HOURLY;
  return useQuery<GridState>({
    queryKey: [
      QUERY_KEYS.STATE,
      {
        aggregate: timeAverage,
        targetDatetime: urlDatetime,
      },
    ],
    queryFn: () => getState(timeAverage, urlDatetime),
  });
};

export default useGetState;
