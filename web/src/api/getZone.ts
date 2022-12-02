import type { UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtom } from 'jotai';
import { useParams } from 'react-router-dom';
import invariant from 'tiny-invariant';
import type { ZoneDetails } from 'types';
import { TimeAverages } from 'utils/constants';
import { timeAverageAtom } from 'utils/state/atoms';
import { getBasePath, getHeaders, QUERY_KEYS, REFETCH_INTERVAL_MS } from './helpers';

const getZone = async (
  timeAverage: TimeAverages,
  zoneId?: string
): Promise<ZoneDetails> => {
  invariant(zoneId, 'Zone ID is required');
  const path = `/v6/details/${timeAverage}/${zoneId}`;
  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  const response = await fetch(`${getBasePath()}${path}`, requestOptions);

  if (response.ok) {
    const { data } = (await response.json()) as { data: ZoneDetails };
    // TODO: app-backend should not return array
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    return data.length > 0 ? data[0] : data;
  }

  throw new Error(await response.text());
};

// TODO: The frontend (graphs) expects that the datetimes in state are the same as in zone
// should we add a check for this?
const useGetZone = (
  options?: UseQueryOptions<ZoneDetails>
): UseQueryResult<ZoneDetails> => {
  const [timeAverage] = useAtom(timeAverageAtom);
  const { zoneId } = useParams();
  return useQuery<ZoneDetails>(
    [QUERY_KEYS.ZONE, zoneId, timeAverage],
    async () => getZone(timeAverage, zoneId),
    {
      staleTime: REFETCH_INTERVAL_MS,
      ...options,
    }
  );
};

export default useGetZone;
