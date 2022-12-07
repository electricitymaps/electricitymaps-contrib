import type { UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtom } from 'jotai';
import type { GridState } from 'types';
import { TimeAverages } from 'utils/constants';
import {
  getBasePath,
  getHeaders,
  QUERY_KEYS,
  REFETCH_INTERVAL_FIVE_MINUTES,
} from './helpers';
import { timeAverageAtom } from 'utils/state/atoms';


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

const useGetState = (options?: UseQueryOptions<GridState>): UseQueryResult<GridState> => {
  const [timeAverage] = useAtom(timeAverageAtom);
  return useQuery<GridState>(
    [QUERY_KEYS.STATE, timeAverage],
    async () => getState(timeAverage),
    {
      staleTime: REFETCH_INTERVAL_FIVE_MINUTES,
      refetchOnWindowFocus: false,
      ...options,
    }
  );
};

export default useGetState;
