import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtom } from 'jotai';
import type { GridState } from 'types';
import { getBasePath, getHeaders, QUERY_KEYS } from './helpers';
import { timeAverageAtom } from 'utils/state/atoms';
import { TimeAverages } from 'utils/constants';

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

const useGetState = (): UseQueryResult<GridState> => {
  const [timeAverage] = useAtom(timeAverageAtom);

  // First fetch last hour only
  const last_hour = useQuery<GridState>(
    [QUERY_KEYS.STATE, { aggregate: 'last_hour' }],
    async () => getState('last_hour'),
    {
      enabled: timeAverage === TimeAverages.HOURLY,
    }
  );

  const hourZeroWasSuccessful = Boolean(last_hour.isLoading === false && last_hour.data);

  const shouldFetchFullState =
    timeAverage !== TimeAverages.HOURLY ||
    hourZeroWasSuccessful ||
    last_hour.isError === true;

  // Then fetch the rest of the data
  const all_data = useQuery<GridState>(
    [QUERY_KEYS.STATE, { aggregate: timeAverage }],
    async () => getState(timeAverage),
    {
      // The query should not execute until the last_hour query is done
      enabled: shouldFetchFullState,
    }
  );
  return all_data.data || timeAverage != 'hourly' ? all_data : last_hour;
};

export default useGetState;
