import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtom } from 'jotai';
import { useParams } from 'react-router-dom';
import invariant from 'tiny-invariant';
import type { ZoneDetails } from 'types';
import { TimeAverages } from 'utils/constants';
import { useGetZoneFromPath } from 'utils/helpers';
import { timeAverageAtom } from 'utils/state/atoms';

import { cacheBuster, getBasePath, getHeaders, isValidDate, QUERY_KEYS } from './helpers';

const getZone = async (
  timeAverage: TimeAverages,
  zoneId?: string,
  datetime?: string
): Promise<ZoneDetails> => {
  invariant(zoneId, 'Zone ID is required');
  const isValidDatetime = datetime && isValidDate(datetime);
  const path: URL = new URL(
    `v8/details/${timeAverage}/${zoneId}${
      isValidDatetime ? `?targetDate=${datetime}` : ''
    }`,
    getBasePath()
  );
  path.searchParams.append('cacheKey', isValidDatetime ? datetime : cacheBuster());

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
  const { urlTimeAverage, urlDatetime } = useParams();
  const [timeAverage] = useAtom(timeAverageAtom);
  console.log('shouldQuersdadyLastHour', urlDatetime, urlTimeAverage);
  return useQuery<ZoneDetails>({
    queryKey: [
      QUERY_KEYS.ZONE,
      {
        zone: zoneId,
        aggregate: urlTimeAverage || timeAverage,
        urlDatetime,
      },
    ],
    queryFn: async () => getZone(timeAverage, zoneId, urlDatetime),
  });
};

export default useGetZone;
