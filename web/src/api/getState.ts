import type { QueryClient, UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtom } from 'jotai';
import type { GridState } from 'types';
import { TimeAverages } from 'utils/constants';
import { timeAverageAtom } from 'utils/state/atoms';
import { QUERY_KEYS, getBasePath, getHeaders } from './helpers';

const getState = async (timeAverage: string): Promise<GridState> => {
  const path = `v6/state/${timeAverage}`;
  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  const response = await fetch(`${getBasePath()}/${path}`, requestOptions);

  if (response.ok) {
    const result = (await response.json()) as GridState;
    return result;
  }

  throw new Error(await response.text());
};

/**
 * Prefetches last_hour state on initial app load
 */
export async function prefetchInitialState(queryClient: QueryClient) {
  await queryClient.prefetchQuery({
    queryKey: [QUERY_KEYS.STATE, { aggregate: 'last_hour' }],
    queryFn: async () => getState('last_hour'),
  });
}

const useGetState = (): UseQueryResult<GridState> => {
  const [timeAverage] = useAtom(timeAverageAtom);

  // First fetch last hour only
  const last_hour = useQuery<GridState>(
    [QUERY_KEYS.STATE, { aggregate: 'last_hour' }],
    async () => getState('last_hour'),
    {
      enabled: timeAverage === TimeAverages.HOURLY,
      suspense: true,
      retry: 3,
    }
  );

  const lastHourWasSuccessful = Boolean(last_hour.isLoading === false && last_hour.data);

  const shouldFetchFullState =
    timeAverage !== TimeAverages.HOURLY ||
    lastHourWasSuccessful ||
    last_hour.isError === true;

  // Then fetch the rest of the data
  const all_data = useQuery<GridState>(
    [QUERY_KEYS.STATE, { aggregate: timeAverage }],
    async () => getState(timeAverage),
    {
      // The query should not execute until the last_hour query is done
      enabled: shouldFetchFullState,
      retry: 3,
    }
  );
  return all_data.data || timeAverage != 'hourly' ? all_data : last_hour;
};

export default useGetState;
