import type { UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import type { GridState, TimeAverages } from 'types';
import { getBasePath, getHeaders, QUERY_KEYS } from './helpers';

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
    staleTime: 1000 * 60 * 5,
    ...options,
  });

export default useGetState;
