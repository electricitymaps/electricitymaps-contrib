import type { UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtom } from 'jotai';
import { useParams } from 'react-router-dom';
import type { ZoneDetails } from 'types';
import { TimeAverages } from 'utils/constants';
import { timeAverageAtom } from 'utils/state';
import { getBasePath, getHeaders, QUERY_KEYS, REFETCH_INTERVAL_MS } from './helpers';

const getZone = async (
  zoneId: string,
  timeAverage: TimeAverages
): Promise<ZoneDetails> => {
  const path = `/v6/details/${timeAverage}/${zoneId}`;
  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  const response = await fetch(`${getBasePath()}${path}`, requestOptions);

  if (response.ok) {
    const { data } = (await response.json()) as { data: ZoneDetails };
    // TODO: Fix this in app-backend
    // @ts-ignore: app-backend should not return array
    return data.length > 0 ? data[0] : data;
  }

  throw new Error(await response.text());
};

const useGetZone = (
  options?: UseQueryOptions<ZoneDetails>
): UseQueryResult<ZoneDetails> => {
  const [timeAverage] = useAtom(timeAverageAtom);
  const { zoneId } = useParams();
  return useQuery<ZoneDetails>(
    [QUERY_KEYS.ZONE, zoneId, timeAverage],
    async () => getZone(zoneId, timeAverage),
    {
      staleTime: REFETCH_INTERVAL_MS,
      ...options,
    }
  );
};

export default useGetZone;
