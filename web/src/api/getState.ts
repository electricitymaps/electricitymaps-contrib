import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtom, useAtomValue } from 'jotai';
import type { GridState } from 'types';
import { isHourlyAtom, timeAverageAtom } from 'utils/state/atoms';

import { cacheBuster, getBasePath, QUERY_KEYS } from './helpers';

const getState = async (timeAverage: string): Promise<GridState> => {
  const path: URL = new URL(`v8/state/${timeAverage}`, getBasePath());
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
  const isHourly = useAtomValue(isHourlyAtom);

  // First fetch last hour only
  const last_hour = useQuery<GridState>({
    queryKey: [QUERY_KEYS.STATE, { aggregate: 'last_hour' }],
    queryFn: async () => getState('last_hour'),
    enabled: isHourly,
  });

  const hourZeroWasSuccessful = Boolean(last_hour.isLoading === false && last_hour.data);

  const shouldFetchFullState =
    !isHourly || hourZeroWasSuccessful || last_hour.isError === true;

  // Then fetch the rest of the data
  const all_data = useQuery<GridState>({
    queryKey: [QUERY_KEYS.STATE, { aggregate: timeAverage }],
    queryFn: async () => getState(timeAverage),

    // The query should not execute until the last_hour query is done
    enabled: shouldFetchFullState,
  });
  return (all_data.data || !isHourly ? all_data : last_hour) ?? {};
};

export default useGetState;
