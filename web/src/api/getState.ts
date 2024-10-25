import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useContext } from 'react';
import type { GridState } from 'types';
import { TimeAverages } from 'utils/constants';

import { RouteContext } from '../App';
import { cacheBuster, getBasePath, isValidDate, QUERY_KEYS } from './helpers';

const getState = async (
  timeAverage: TimeAverages,
  targetDatetime?: string
): Promise<GridState> => {
  const isValidDatetime = targetDatetime && isValidDate(targetDatetime);
  const path: URL = new URL(
    `v8/state/${timeAverage}${isValidDatetime ? `?targetDate=${targetDatetime}` : ''}`,
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
  const { urlTimeAverage = TimeAverages.HOURLY, urlDatetime } = useContext(RouteContext);

  return useQuery<GridState>({
    queryKey: [
      QUERY_KEYS.STATE,
      {
        aggregate: urlTimeAverage,
        targetDatetime: urlDatetime,
      },
    ],
    queryFn: () => getState(urlTimeAverage, urlDatetime),
  });
};

export default useGetState;
