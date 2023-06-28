import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtom } from 'jotai';
import { useParams } from 'react-router-dom';
import invariant from 'tiny-invariant';
import type { ZoneDetails } from 'types';
import { TimeAverages } from 'utils/constants';
import { timeAverageAtom } from 'utils/state/atoms';

import { getBasePath, getHeaders, QUERY_KEYS } from './helpers';

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
    if (!data.zoneStates) {
      throw new Error('No data returned from API');
    }
    return data;
  }

  throw new Error(await response.text());
};

// TODO: The frontend (graphs) expects that the datetimes in state are the same as in zone
// should we add a check for this?
const useGetZone = (): UseQueryResult<ZoneDetails> => {
  const { zoneId } = useParams();
  const [timeAverage] = useAtom(timeAverageAtom);
  return useQuery<ZoneDetails>(
    [QUERY_KEYS.ZONE, { zone: zoneId, aggregate: timeAverage }],
    async () => getZone(timeAverage, zoneId)
  );
};

export default useGetZone;
