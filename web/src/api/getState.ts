import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtom, useAtomValue } from 'jotai';
import { useParams } from 'react-router-dom';
import type { GridState } from 'types';
import { hasPathTimeAverageAndDatetime, parsePath } from 'utils/pathUtils';
import { isHourlyAtom, timeAverageAtom } from 'utils/state/atoms';

import { cacheBuster, getBasePath, isValidDate, QUERY_KEYS } from './helpers';

const getState = async (timeAverage: string, datetime?: string): Promise<GridState> => {
  const isValidDatetime = datetime && isValidDate(datetime);
  const path: URL = new URL(
    `v8/state/${timeAverage}${isValidDatetime ? `?targetDate=${datetime}` : ''}`,
    getBasePath()
  );
  // const path: URL = new URL(`v8/state/${timeAverage}`, getBasePath());

  path.searchParams.append('cacheKey', cacheBuster());

  const response = await fetch(path);

  if (response.ok) {
    const result = (await response.json()) as GridState;
    return result;
  }

  throw new Error(await response.text());
};

const useGetState = (): UseQueryResult<GridState> => {
  const [timeAverage] = useAtom(timeAverageAtom);
  const parsedPath = parsePath(location.pathname);

  const isHourly = useAtomValue(isHourlyAtom);
  const isHistoricalQuery = hasPathTimeAverageAndDatetime(location.pathname);

  const shouldQueryLastHour = isHourly && !isHistoricalQuery;
  // First fetch last hour only
  console.log(
    'shouldQueryLastHour',
    shouldQueryLastHour,
    parsedPath?.datetime,
    parsedPath?.timeAverage
  );
  const last_hour = useQuery<GridState>({
    queryKey: [QUERY_KEYS.STATE, { aggregate: 'last_hour' }],
    queryFn: async () => getState('last_hour'),
    enabled: shouldQueryLastHour,
  });

  const hourZeroWasSuccessful = Boolean(last_hour.isLoading === false && last_hour.data);

  const shouldFetchFullState =
    isHistoricalQuery || !isHourly || hourZeroWasSuccessful || last_hour.isError === true;
  // Then fetch the rest of the data
  const all_data = useQuery<GridState>({
    queryKey: [
      QUERY_KEYS.STATE,
      {
        aggregate: parsedPath?.timeAverage || timeAverage,
        datetime: parsedPath?.datetime,
      },
    ],
    queryFn: async () => getState(timeAverage, parsedPath?.datetime),

    // The query should not execute until the last_hour query is done
    enabled: shouldFetchFullState,
  });
  return (all_data.data || !isHourly ? all_data : last_hour) ?? {};
};

export default useGetState;
