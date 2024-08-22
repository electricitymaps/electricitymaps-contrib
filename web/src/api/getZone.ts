import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtom } from 'jotai';
import invariant from 'tiny-invariant';
import type { ZoneDetails } from 'types';
import { TimeAverages } from 'utils/constants';
import { useGetZoneFromPath } from 'utils/helpers';
import { timeAverageAtom } from 'utils/state/atoms';

import { cacheBuster, getBasePath, getHeaders, QUERY_KEYS } from './helpers';

const getZone = async (
  timeAverage: TimeAverages,
  zoneId?: string,
  startDate?: string,
  endDate?: string
): Promise<ZoneDetails> => {
  invariant(zoneId, 'Zone ID is required');
  const path: URL = new URL(`v8/details/${timeAverage}/${zoneId}`, getBasePath());
  path.searchParams.append('cacheKey', cacheBuster());

  if (startDate) {
    path.searchParams.append('startDate', startDate);
  }
  if (endDate) {
    path.searchParams.append('endDate', endDate);
  }

  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  const response = await fetch(path, requestOptions);

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
  const zoneId = useGetZoneFromPath();
  const [timeAverage] = useAtom(timeAverageAtom);

  // Get startDate and endDate from URL params
  const urlParameters = new URLSearchParams(window.location.search);
  const startDate = urlParameters.get('startDate') || undefined;
  const endDate = urlParameters.get('endDate') || undefined;

  return useQuery<ZoneDetails>({
    queryKey: [
      QUERY_KEYS.ZONE,
      { zone: zoneId, aggregate: timeAverage, startDate, endDate },
    ],
    queryFn: async () => getZone(timeAverage, zoneId, startDate, endDate),
  });
};

export default useGetZone;
