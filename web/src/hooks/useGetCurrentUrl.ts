import { useParams } from 'react-router-dom';
import { RouteParameters, ZoneKey } from 'types';
import { baseUrl } from 'utils/constants';

export function useGetCurrentUrl({ zoneId }: { zoneId?: ZoneKey }) {
  const {
    urlTimeAverage,
    urlDatetime,
    zoneId: zoneIdParameter,
  } = useParams<RouteParameters>();
  const zId = zoneId || zoneIdParameter;
  const url =
    baseUrl +
    (zId
      ? `/zone/${zId}/${urlTimeAverage}/${urlDatetime || new Date().toISOString()}`
      : '/map/24h');

  return url;
}
