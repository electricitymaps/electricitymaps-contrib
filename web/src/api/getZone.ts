import type { UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import type { TimeAverages, ZoneDetails } from 'types';
import { getHeaders, getBasePath, QUERY_KEYS, REFETCH_INTERVAL_MS } from './helpers';

const getZone = async (zoneId: string, timeAverage: TimeAverages): Promise<ZoneDetails> => {
  const path = `/v5/history/${timeAverage}?countryCode=${zoneId}`;
  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  const response = await fetch(`${getBasePath()}/${path}`, requestOptions);

  if (response.ok) {
    const { data } = (await response.json()) as { data: ZoneDetails };
    return data;
  }

  throw new Error(await response.text());
};

const useGetZone = (
  timeAverage: TimeAverages,
  zoneId: string,
  options?: UseQueryOptions<ZoneDetails>
): UseQueryResult<ZoneDetails> =>
  useQuery<ZoneDetails>([QUERY_KEYS.ZONE, zoneId], async () => getZone(zoneId, timeAverage), {
    staleTime: REFETCH_INTERVAL_MS,
    ...options,
  });

export default useGetZone;
