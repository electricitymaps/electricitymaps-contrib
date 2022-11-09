import type { UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import type { GridState } from 'types';
import { TimeAverages } from 'utils/constants';
import { getBasePath, getHeaders, QUERY_KEYS, REFETCH_INTERVAL_MS } from './helpers';

const getState = async (timeAverage: string): Promise<GridState> => {
  const path = `/v5/state/${timeAverage}`;
  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  const response = await fetch(`${getBasePath()}/${path}`, requestOptions);

  if (response.ok) {
    const { data } = (await response.json()) as { data: GridState };
    return data;
  }

  throw new Error(await response.text());
};

const useGetState = (timeAverage: TimeAverages, options?: UseQueryOptions<GridState>): UseQueryResult<GridState> =>
  useQuery<GridState>([QUERY_KEYS.STATE, timeAverage], async () => getState(timeAverage), {
    staleTime: REFETCH_INTERVAL_MS,
    ...options,
  });

export default useGetState;
